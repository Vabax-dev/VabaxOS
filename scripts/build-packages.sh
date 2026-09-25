#!/usr/bin/env bash
# Builds the VabaxOS Debian packages in packages/ (ADR-0008).
#   ./scripts/build-packages.sh OUTPUT_DIR
# Each packages/<name>/ has:
#   control           the DEBIAN/control file, without Version (added here)
#   root/             the files to install, as they will be on the system
#   postinst, postrm  maintainer scripts (optional)
#   triggers          dpkg triggers (optional)
#   fetch             large files downloaded at build time, one per line:
#                     URL SHA256 PATH (optional; kept in cache/downloads)
#   copyright         licence of the contents (optional, default GPL-3.0+)
#   po/*.po           translations of the domain <name> (optional)
# No root needed: files belong to root:root inside the package.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:?Uso: build-packages.sh CARTELLA_DI_USCITA}"
# Until the Vabax APT repository exists (v0.2), packages go only in the ISO.
VERSION="0.1.0~dev"

mkdir -p "$OUT"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Same timestamps in every build, so the ISO stays reproducible: the date of
# the last commit, or, outside a Git checkout, the snapshot date of the ISO.
if [[ -z "${SOURCE_DATE_EPOCH:-}" ]]; then
    SOURCE_DATE_EPOCH="$(git -C "$REPO" log -1 --format=%ct 2>/dev/null || true)"
fi
if [[ -z "$SOURCE_DATE_EPOCH" ]]; then
    # shellcheck source=/dev/null
    . "$REPO/image/build.conf"
    SOURCE_DATE_EPOCH="$(date -u -d "$(sed -E 's/^(....)(..)(..)T(..)(..)(..)Z$/\1-\2-\3 \4:\5:\6 UTC/' <<< "$VABAXOS_SNAPSHOT")" +%s)"
fi
export SOURCE_DATE_EPOCH

for dir in "$REPO"/packages/*/; do
    name="$(basename "$dir")"
    [[ -f "$dir/control" ]] || continue
    tree="$TMP/$name"
    mkdir -p "$tree/DEBIAN"
    cp -a "$dir/root/." "$tree/"
    find "$tree" -name __pycache__ -prune -exec rm -rf {} +
    compress=(-Zxz)
    if [[ -f "$dir/fetch" ]]; then
        # Models and similar files are too big for Git: downloaded once,
        # checked against the SHA-256 in the fetch file, kept in cache/.
        downloads="$REPO/cache/downloads"
        mkdir -p "$downloads"
        while read -r url sha path; do
            [[ -z "$url" || "$url" == \#* ]] && continue
            file="$downloads/$sha"
            if [[ ! -f "$file" ]]; then
                printf 'Scarico %s\n' "$url"
                curl -fsSL --retry 3 -o "$file.part" "$url"
                mv "$file.part" "$file"
            fi
            if ! printf '%s  %s\n' "$sha" "$file" | sha256sum -c --quiet; then
                rm -f "$file"
                printf 'ERRORE: %s non corrisponde all'\''impronta attesa.\n' "$url" >&2
                exit 1
            fi
            install -D -m 0644 "$file" "$tree/$path"
        done < "$dir/fetch"
        # Neural network weights do not compress: save the build time.
        compress=(-Zzstd -z1)
    fi
    # Files in /etc are configuration: dpkg keeps the user's changes.
    if [[ -d "$tree/etc" ]]; then
        (cd "$tree" && find etc -type f | sort | sed 's|^|/|') > "$tree/DEBIAN/conffiles"
    fi
    { cat "$dir/control"; printf 'Version: %s\n' "$VERSION"; } > "$tree/DEBIAN/control"
    for script in postinst postrm; do
        if [[ -f "$dir/$script" ]]; then
            install -m 0755 "$dir/$script" "$tree/DEBIAN/$script"
        fi
    done
    if [[ -f "$dir/triggers" ]]; then
        install -m 0644 "$dir/triggers" "$tree/DEBIAN/triggers"
    fi
    if compgen -G "$dir/po/*.po" >/dev/null; then
        for po in "$dir"/po/*.po; do
            lang="$(basename "$po" .po)"
            mo="$tree/usr/share/locale/$lang/LC_MESSAGES/$name.mo"
            mkdir -p "$(dirname "$mo")"
            if command -v msgfmt >/dev/null; then
                msgfmt --check -o "$mo" "$po"
            else
                python3 "$REPO/scripts/lib/po2mo.py" "$po" "$mo"
            fi
        done
    fi
    # Licence of the package contents (ADR-0011).
    mkdir -p "$tree/usr/share/doc/$name"
    if [[ -f "$dir/copyright" ]]; then
        install -m 0644 "$dir/copyright" "$tree/usr/share/doc/$name/copyright"
    else
        printf 'VabaxOS: %s\nCopyright 2026 Vabax and VabaxOS contributors\nLicense: GPL-3.0-or-later, see /usr/share/common-licenses/GPL-3\n' \
            "$name" > "$tree/usr/share/doc/$name/copyright"
    fi
    find "$tree" -exec touch --no-dereference -d "@$SOURCE_DATE_EPOCH" {} +
    dpkg-deb --root-owner-group "${compress[@]}" --build "$tree" "$OUT/${name}_${VERSION}_all.deb" >/dev/null
    printf 'Pacchetto: %s\n' "$OUT/${name}_${VERSION}_all.deb"
done
