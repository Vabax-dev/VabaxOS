#!/usr/bin/env bash
# Creates the OpenPGP keys of VabaxOS (ADR-0020), on Vabax's computer:
#   bash scripts/crea-chiavi.sh archivio   # the key of the APT archive
#   bash scripts/crea-chiavi.sh versioni   # the key of the official releases
#
# Both are Ed25519 keys, kept in the GnuPG keyring of the user (~/.gnupg);
# only the public keys are written in keys/, for the repository.
# - archivio: without passphrase, because GitHub Actions signs the archive
#   with it (secret VABAXOS_ARCHIVE_KEY). The secret key is copied to the
#   Windows clipboard (clip.exe), to paste it in the secret on GitHub; it is
#   never printed.
# - versioni: with a passphrase, asked in this terminal (no graphical
#   window), never written anywhere. It signs SHA256SUMS of the releases.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KIND="${1:-}"
case "$KIND" in
    archivio)
        uid="VabaxOS archive signing key"
        file="$REPO/keys/vabaxos-archive.asc"
        expire=3y
        ;;
    versioni)
        uid="VabaxOS release signing key"
        file="$REPO/keys/vabaxos-release.asc"
        expire=2y
        ;;
    *)
        printf 'Uso: bash scripts/crea-chiavi.sh archivio|versioni\n' >&2
        exit 2
        ;;
esac

command -v gpg >/dev/null || { printf 'Manca gpg: sudo apt install gnupg\n' >&2; exit 1; }
if gpg --batch --list-secret-keys "=$uid" >/dev/null 2>&1; then
    printf 'La chiave «%s» esiste già: non ne creo un'\''altra.\n' "$uid" >&2
    exit 1
fi

if [[ "$KIND" == archivio ]]; then
    gpg --batch --quiet --passphrase '' --quick-generate-key "$uid" ed25519 sign "$expire"
else
    printf 'Ora GnuPG chiede due volte la passphrase della chiave delle versioni.\n'
    printf 'Scegline una lunga e conservala: senza, non si possono firmare le versioni.\n'
    gpg --quiet --pinentry-mode loopback --quick-generate-key "$uid" ed25519 sign "$expire"
fi
fingerprint="$(gpg --batch --with-colons --list-secret-keys "=$uid" | awk -F: '$1 == "fpr" {print $10; exit}')"

mkdir -p "$REPO/keys"
gpg --batch --armor --export "$fingerprint" > "$file"
printf 'Chiave creata. Impronta: %s\n' "$fingerprint"
printf 'Chiave pubblica scritta in %s\n' "${file#"$REPO"/}"

if [[ "$KIND" == archivio ]]; then
    if command -v clip.exe >/dev/null; then
        gpg --batch --armor --export-secret-keys "$fingerprint" | clip.exe
        printf 'La chiave segreta è negli appunti di Windows: incollala nel segreto VABAXOS_ARCHIVE_KEY su GitHub, poi copia qualcos'\''altro per toglierla dagli appunti.\n'
    else
        printf 'clip.exe non trovato: la chiave segreta resta solo in ~/.gnupg.\n'
    fi
fi
