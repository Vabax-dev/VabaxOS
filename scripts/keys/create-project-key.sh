#!/usr/bin/env bash
# Creates the key of the VabaxOS project (ADR-0026): an OpenPGP Ed25519
# key that only certifies, valid 5 years, and a subkey that signs, valid 2
# years. It signs the VabaxOS APT archive and SHA256SUMS of the ISO
# (ADR-0015). Vabax runs it once, in the Debian window of the workstation:
#   bash scripts/keys/create-project-key.sh
# The passphrase is asked here twice, as plain questions a screen reader
# reads (no graphical dialog), not shown, and given to gpg through a pipe:
# it never goes anywhere else.
# Writes keys/vabaxos-project.asc (the public key, for the repository) and,
# in a folder of your choice (a USB stick), a backup of the secret key and
# its revocation certificate.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PUBLIC="$REPO/keys/vabaxos-project.asc"
NAME="VabaxOS Project Signing Key"
EMAIL="${VABAXOS_KEY_EMAIL:-info@vabax.it}"

say() { printf '%s\n' "$@"; }

if [[ -f "$PUBLIC" ]]; then
    say "La chiave del progetto esiste già: $PUBLIC" "Non ne creo un'altra."
    exit 1
fi
say "Creo la chiave del progetto VabaxOS:" \
    "  nome: $NAME" \
    "  indirizzo: $EMAIL" \
    "Serve a firmare l'archivio APT e le ISO di VabaxOS." \
    "Ti chiedo una passphrase, due volte: sceglila lunga, per esempio" \
    "quattro o cinque parole a caso, e conservala. Senza non si firma più." \
    "Mentre la scrivi non compare niente sullo schermo."
read -r -p "Continuo? Scrivi s e premi Invio: " answer
[[ "$answer" == s || "$answer" == S ]] || { say "Non ho fatto niente."; exit 0; }

while true; do
    read -rs -p "Passphrase: " passphrase; printf '\n'
    read -rs -p "Scrivila di nuovo: " again; printf '\n'
    if [[ -z "$passphrase" ]]; then
        say "La passphrase è vuota: riprova."
    elif [[ "$passphrase" != "$again" ]]; then
        say "Le due passphrase sono diverse: riprova."
    elif (( ${#passphrase} < 12 )); then
        say "Troppo corta: almeno 12 caratteri. Riprova."
    else
        break
    fi
done
unset again
# gpg reads the passphrase from a pipe (file descriptor 3).
gpg_with_passphrase() {
    gpg --batch --pinentry-mode loopback --passphrase-fd 3 "$@" 3< <(printf '%s' "$passphrase")
}

say "Creo la chiave (qualche secondo)."
gpg_with_passphrase --quick-generate-key "$NAME <$EMAIL>" ed25519 cert 5y
FPR="$(gpg --batch --with-colons --list-keys "$NAME <$EMAIL>" | awk -F: '$1 == "fpr" {print $10; exit}')"
gpg_with_passphrase --quick-add-key "$FPR" ed25519 sign 2y

mkdir -p "$(dirname "$PUBLIC")"
gpg --batch --armor --export "$FPR" > "$PUBLIC"
say "Chiave pubblica: $PUBLIC"

say "Ora la copia di sicurezza della chiave segreta, protetta dalla passphrase." \
    "Scrivi una cartella su una chiavetta, per esempio /mnt/e per la chiavetta E: di Windows," \
    "oppure premi solo Invio per farla dopo."
read -r -p "Cartella: " backup
if [[ -n "$backup" ]]; then
    mkdir -p "$backup"
    gpg_with_passphrase --armor --export-secret-keys "$FPR" > "$backup/vabaxos-project-secret.asc"
    revocation="${GNUPGHOME:-$HOME/.gnupg}/openpgp-revocs.d/$FPR.rev"
    [[ -f "$revocation" ]] && cp "$revocation" "$backup/vabaxos-project-revocation.rev"
    say "Copia di sicurezza in $backup: vabaxos-project-secret.asc e vabaxos-project-revocation.rev." \
        "Tieni la chiavetta in un posto sicuro, lontana dal computer."
fi

unset passphrase
# The fingerprint in groups of four characters, easier to read aloud.
say "Impronta della chiave (da pubblicare e da confrontare):" \
    "  $(fold -w4 <<< "$FPR" | paste -sd' ')"
