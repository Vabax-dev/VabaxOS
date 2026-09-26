#!/usr/bin/env bash
# Signs SHA256SUMS of a VabaxOS release with the project key (ADR-0015,
# ADR-0026), then checks the signature with the public key of the
# repository, as whoever downloads the ISO will.
#   ./scripts/sign-release.sh [FOLDER]     (default: out)
# Writes FOLDER/SHA256SUMS.sign (detached, armored, as Debian does).
# gpg asks the passphrase in this window.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR="${1:-$REPO/out}"
PUBLIC="${VABAXOS_ARCHIVE_KEY:-$REPO/keys/vabaxos-project.asc}"

[[ -f "$DIR/SHA256SUMS" ]] || { printf 'ERRORE: manca %s/SHA256SUMS.\n' "$DIR" >&2; exit 1; }
[[ -f "$PUBLIC" ]] || { printf 'ERRORE: manca la chiave del progetto (%s).\n' "$PUBLIC" >&2; exit 1; }
KEY="$(gpg --batch --with-colons --show-keys "$PUBLIC" | awk -F: '$1 == "fpr" {print $10; exit}')"

# Every file listed must be there and match, before signing.
(cd "$DIR" && sha256sum --check --quiet SHA256SUMS)
gpg --pinentry-mode loopback --yes --local-user "$KEY" --digest-algo SHA512 \
    --armor --detach-sign --output "$DIR/SHA256SUMS.sign" "$DIR/SHA256SUMS"

KEYRING="$(mktemp)"
trap 'rm -f "$KEYRING"' EXIT
gpg --batch --dearmor < "$PUBLIC" > "$KEYRING"
if gpgv --keyring "$KEYRING" "$DIR/SHA256SUMS.sign" "$DIR/SHA256SUMS" 2>/dev/null; then
    printf 'Firmato: %s/SHA256SUMS.sign\nFirma controllata con %s\n' "$DIR" "$PUBLIC"
else
    printf 'ERRORE: la firma non si verifica con %s.\n' "$PUBLIC" >&2
    exit 1
fi
