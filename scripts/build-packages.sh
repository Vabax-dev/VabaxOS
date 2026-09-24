#!/usr/bin/env bash
# Builds the VabaxOS Debian packages in packages/ (ADR-0008).
#   ./scripts/build-packages.sh OUTPUT_DIR
# Each packages/<name>/ has:
#   control           the DEBIAN/control file, without Version (added here)
#   root/             the files to install, as they will be on the system
#   postinst, postrm  maintainer scripts (optional)
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

# Same timestamps in every build, so the ISO stays reproducible.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(git -C "$REPO" log -1 --format=%ct)}"

for dir in "$REPO"/packages/*/; do
    name="$(basename "$dir")"
    [[ -f "$dir/control" ]] || continue
    tree="$TMP/$name"
    mkdir -p "$tree/DEBIAN"
    cp -a "$dir/root/." "$tree/"
    find "$tree" -name __pycache__ -prune -exec rm -rf {} +
    { cat "$dir/control"; printf 'Version: %s\n' "$VERSION"; } > "$tree/DEBIAN/control"
    for script in postinst postrm; do
        if [[ -f "$dir/$script" ]]; then
            install -m 0755 "$dir/$script" "$tree/DEBIAN/$script"
        fi
    done
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
    printf 'VabaxOS: %s\nCopyright 2026 Vabax and VabaxOS contributors\nLicense: GPL-3.0-or-later, see /usr/share/common-licenses/GPL-3\n' \
        "$name" > "$tree/usr/share/doc/$name/copyright"
    find "$tree" -exec touch --no-dereference -d "@$SOURCE_DATE_EPOCH" {} +
    dpkg-deb --root-owner-group -Zxz --build "$tree" "$OUT/${name}_${VERSION}_all.deb" >/dev/null
    printf 'Pacchetto: %s\n' "$OUT/${name}_${VERSION}_all.deb"
done
