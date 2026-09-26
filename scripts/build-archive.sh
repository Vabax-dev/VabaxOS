#!/usr/bin/env bash
# Builds the VabaxOS APT archive (ADR-0020) from the packages in packages/.
#   ./scripts/build-archive.sh [--unsigned] OUTPUT_DIR
#
# The archive is rebuilt whole every time, with the current version of each
# package: nothing has to be kept between two publications. GitHub Pages
# takes no file over 100 MB, so larger packages are left out: the Kokoro
# model (vabaxos-kokoro-model, about 330 MB, fixed version) comes only with
# the ISO, and a new model will need another way.
#
# It is signed with the secret key in the environment variable
# VABAXOS_ARCHIVE_KEY (ASCII armour, without passphrase: in the CI a GitHub
# secret), whose public key must be keys/vabaxos-archive.asc. --unsigned
# builds it without signature, only for tests (apt refuses it otherwise).
#
# Layout: OUTPUT_DIR/dists/vabaxos/..., OUTPUT_DIR/pool/..., and the public
# key as OUTPUT_DIR/vabaxos-archive.asc.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SIGNED=true
if [[ "${1:-}" == --unsigned ]]; then
    SIGNED=false
    shift
fi
OUT="${1:?Uso: build-archive.sh [--unsigned] CARTELLA_DI_USCITA}"

for tool in reprepro gpg dpkg-deb; do
    command -v "$tool" >/dev/null || { printf 'ERRORE: manca %s.\n' "$tool" >&2; exit 1; }
done

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
"$REPO/scripts/build-packages.sh" "$TMP/debs" >/dev/null

mkdir -p "$TMP/conf"
cat > "$TMP/conf/distributions" <<EOF
Origin: VabaxOS
Label: VabaxOS
Suite: vabaxos
Codename: vabaxos
Architectures: amd64
Components: main
Description: VabaxOS packages (ADR-0020)
EOF

if [[ "$SIGNED" == true ]]; then
    [[ -n "${VABAXOS_ARCHIVE_KEY:-}" ]] || { printf 'ERRORE: VABAXOS_ARCHIVE_KEY non è impostata.\n' >&2; exit 1; }
    [[ -f "$REPO/keys/vabaxos-archive.asc" ]] || { printf 'ERRORE: manca keys/vabaxos-archive.asc.\n' >&2; exit 1; }
    export GNUPGHOME="$TMP/gnupg"
    mkdir -m 0700 "$GNUPGHOME"
    printf '%s\n' "$VABAXOS_ARCHIVE_KEY" | gpg --batch --quiet --import
    fingerprint="$(gpg --batch --with-colons --list-secret-keys | awk -F: '$1 == "fpr" {print $10; exit}')"
    # The secret key must match the public key that the packages carry,
    # or every installed system would refuse the archive.
    public="$(gpg --batch --with-colons --show-keys "$REPO/keys/vabaxos-archive.asc" | awk -F: '$1 == "fpr" {print $10}')"
    grep -qx "$fingerprint" <<< "$public" \
        || { printf 'ERRORE: la chiave segreta non corrisponde a keys/vabaxos-archive.asc.\n' >&2; exit 1; }
    printf 'SignWith: %s\n' "$fingerprint" >> "$TMP/conf/distributions"
    # A key past its date stops the updates of every installed system, and
    # they get a longer date only with an update of vabaxos-apt: warn well
    # before (docs/sviluppo/chiavi.md, "Quando una chiave scade").
    expires="$(gpg --batch --with-colons --show-keys "$REPO/keys/vabaxos-archive.asc" | awk -F: '$1 == "pub" {print $7; exit}')"
    if [[ -n "$expires" ]] && (( expires - $(date +%s) < 180 * 86400 )); then
        printf '::warning::La chiave dell'"'"'archivio scade il %s: allungala (docs/sviluppo/chiavi.md).\n' \
            "$(date -u -d "@$expires" +%Y-%m-%d)"
    fi
fi

rm -rf "$OUT"
mkdir -p "$OUT"
for deb in "$TMP"/debs/*.deb; do
    if (( $(stat -c %s "$deb") > 95 * 1024 * 1024 )); then
        printf 'Escluso (più di 95 MB, solo nella ISO): %s\n' "$(basename "$deb")"
        rm "$deb"
    fi
done
reprepro --silent --basedir "$TMP" --outdir "$OUT" includedeb vabaxos "$TMP"/debs/*.deb
if [[ -f "$REPO/keys/vabaxos-archive.asc" ]]; then
    install -m 0644 "$REPO/keys/vabaxos-archive.asc" "$OUT/vabaxos-archive.asc"
fi
printf 'Archivio: %s (%s pacchetti)\n' "$OUT" "$(find "$OUT/pool" -name '*.deb' | wc -l)"
