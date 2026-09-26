#!/usr/bin/env bash
# Builds the VabaxOS APT archive from the VabaxOS packages, signed with the
# project key (ADR-0026).
#   ./scripts/apt-repo.sh [--packages DIR] [--out DIR] [--key FINGERPRINT]
# --packages: the .deb files (default out/packages, made here if missing)
# --out:      the archive (default out/apt), made again every time
# --key:      the signing key (default: the one in keys/vabaxos-project.asc)
# GNUPGHOME chooses the keyring, as for gpg (tests use a throwaway one).
# gpg asks the passphrase in this window: it never goes anywhere else.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGES="$REPO/out/packages"
OUT="$REPO/out/apt"
KEY=""
SUITE="forky"
COMPONENT="main"

while (($#)); do
    case "$1" in
        --packages) PACKAGES="${2:?--packages vuole una cartella}"; shift ;;
        --out) OUT="${2:?--out vuole una cartella}"; shift ;;
        --key) KEY="${2:?--key vuole una impronta}"; shift ;;
        -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
        *) printf 'Opzione sconosciuta: %s\n' "$1" >&2; exit 2 ;;
    esac
    shift
done

if [[ -z "$KEY" ]]; then
    if [[ ! -f "$REPO/keys/vabaxos-project.asc" ]]; then
        printf 'ERRORE: manca la chiave del progetto (keys/vabaxos-project.asc).\n' >&2
        printf 'Si crea con scripts/keys/create-project-key.sh, oppure si sceglie con --key.\n' >&2
        exit 1
    fi
    KEY="$(gpg --batch --with-colons --show-keys "$REPO/keys/vabaxos-project.asc" | awk -F: '$1 == "fpr" {print $10; exit}')"
fi
if ! gpg --batch --list-secret-keys "$KEY" >/dev/null 2>&1; then
    printf 'ERRORE: la chiave segreta %s non è in questo computer.\n' "$KEY" >&2
    exit 1
fi

if ! compgen -G "$PACKAGES/vabaxos-*.deb" >/dev/null; then
    printf 'Costruisco i pacchetti in %s\n' "$PACKAGES"
    "$REPO/scripts/build-packages.sh" "$PACKAGES" >/dev/null
fi

rm -rf "$OUT"
mkdir -p "$OUT/pool/$COMPONENT" "$OUT/dists/$SUITE/$COMPONENT/binary-all" "$OUT/dists/$SUITE/$COMPONENT/binary-amd64"
cp "$PACKAGES"/vabaxos-*.deb "$OUT/pool/$COMPONENT/"

cd "$OUT"
# Packages for "all", and an empty list for amd64, which APT also asks for.
apt-ftparchive packages "pool/$COMPONENT" > "dists/$SUITE/$COMPONENT/binary-all/Packages"
: > "dists/$SUITE/$COMPONENT/binary-amd64/Packages"
for list in dists/"$SUITE"/"$COMPONENT"/binary-*/Packages; do
    gzip -9 -n -k "$list"
    xz -9 -k "$list"
done
apt-ftparchive \
    -o "APT::FTPArchive::Release::Origin=VabaxOS" \
    -o "APT::FTPArchive::Release::Label=VabaxOS" \
    -o "APT::FTPArchive::Release::Suite=$SUITE" \
    -o "APT::FTPArchive::Release::Codename=$SUITE" \
    -o "APT::FTPArchive::Release::Architectures=amd64 all" \
    -o "APT::FTPArchive::Release::Components=$COMPONENT" \
    -o "APT::FTPArchive::Release::Description=VabaxOS packages (ADR-0026)" \
    release "dists/$SUITE" > "dists/$SUITE/Release.tmp"
mv "dists/$SUITE/Release.tmp" "dists/$SUITE/Release"

# InRelease (Release signed inline) and Release.gpg (detached), as Debian.
gpg --batch --yes --local-user "$KEY" --digest-algo SHA512 --clearsign \
    --output "dists/$SUITE/InRelease" "dists/$SUITE/Release"
gpg --batch --yes --local-user "$KEY" --digest-algo SHA512 --armor --detach-sign \
    --output "dists/$SUITE/Release.gpg" "dists/$SUITE/Release"
gpg --batch --armor --export "$KEY" > "$OUT/vabaxos-archive-keyring.asc"

printf 'Archivio: %s\n' "$OUT"
printf 'Pacchetti: %s\n' "$(find "pool/$COMPONENT" -name '*.deb' | wc -l)"
printf 'Firmato con: %s\n' "$KEY"
