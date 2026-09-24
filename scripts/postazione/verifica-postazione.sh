#!/usr/bin/env bash
# Checks that the VabaxOS development workstation is ready (ADR-0013).
#   bash ~/projects/VabaxOS/scripts/postazione/verifica-postazione.sh
# Prints one line per check, starting with OK or PROBLEMA, and says the result aloud.
# Exit status: number of problems found (0 means ready).
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_LIST="$HERE/pacchetti-debian.txt"
DEST="$HOME/projects/VabaxOS"
PROBLEMS=0

ok() { printf 'OK: %s\n' "$*"; }
problem() {
    printf 'PROBLEMA: %s\n' "$*"
    PROBLEMS=$((PROBLEMS + 1))
}

printf 'Verifica della postazione VabaxOS\n\n'

# shellcheck source=/dev/null
. /etc/os-release
if [[ "${VERSION_CODENAME:-}" == trixie ]]; then
    ok "Debian 13 trixie."
else
    problem "Serve Debian 13 trixie, questa è ${PRETTY_NAME:-sconosciuta}. Esegui prepara-debian.sh."
fi

if grep -qi microsoft /proc/version 2>/dev/null; then
    if [[ -d /mnt/wslg ]] || [[ "$(uname -r)" == *WSL2* ]]; then
        ok "WSL 2."
    else
        problem "Sembra WSL 1. In PowerShell esegui: wsl --set-version Debian 2"
    fi
fi

if [[ -f "$PKG_LIST" ]]; then
    MISSING=()
    while read -r pkg; do
        dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q 'install ok installed' || MISSING+=("$pkg")
    done < <(grep -Ev '^[[:space:]]*(#|$)' "$PKG_LIST")
    if [[ ${#MISSING[@]} -eq 0 ]]; then
        ok "Tutti i pacchetti della postazione sono installati."
    else
        problem "Mancano questi pacchetti: ${MISSING[*]}. Esegui prepara-debian.sh."
    fi
else
    problem "Non trovo l'elenco dei pacchetti: $PKG_LIST"
fi

if [[ -e /dev/kvm ]]; then
    if [[ -r /dev/kvm && -w /dev/kvm ]]; then
        ok "KVM disponibile: le macchine virtuali saranno veloci."
    else
        problem "/dev/kvm esiste ma non hai i permessi. Chiudi WSL con wsl --shutdown e riapri Debian."
    fi
else
    problem "/dev/kvm non esiste: manca la virtualizzazione annidata. Vedi la guida, sezione Problemi comuni."
fi

if compgen -G '/usr/share/OVMF/OVMF_CODE*.fd' >/dev/null; then
    ok "Firmware UEFI per QEMU (OVMF) presente."
else
    problem "Firmware OVMF mancante. Installa il pacchetto ovmf."
fi

if sudo -n /usr/bin/lb --version >/dev/null 2>&1; then
    ok "Claude può costruire la ISO senza chiedere la password."
else
    printf 'AVVISO: il comando lb chiede la password. Claude ti chiederà di costruire la ISO a mano.\n'
fi

if git config --global user.name >/dev/null && git config --global user.email >/dev/null; then
    ok "Git configurato: $(git config --global user.name)."
else
    problem "Git non ha nome ed email per i commit. Esegui prepara-debian.sh."
fi

if [[ -d "$DEST/.git" ]]; then
    ok "Repository presente in $DEST."
else
    problem "Repository non trovato in $DEST."
fi

if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
    ok "Accesso a GitHub attivo."
else
    problem "Non sei collegato a GitHub. Esegui: gh auth login, poi: gh auth setup-git"
fi

FREE_GB=$(df -Pk "$HOME" | awk 'NR==2 {print int($4 / 1048576)}')
if [[ "$FREE_GB" -ge 40 ]]; then
    ok "Spazio libero: $FREE_GB GB."
else
    problem "Spazio libero: solo $FREE_GB GB. Ne servono almeno 40 per costruire e provare la ISO."
fi

MEM_GB=$(awk '/MemTotal/ {print int($2 / 1048576 + 0.5)}' /proc/meminfo)
if [[ "$MEM_GB" -ge 6 ]]; then
    ok "Memoria per WSL: $MEM_GB GB."
else
    problem "Memoria per WSL: solo $MEM_GB GB. Ne servono almeno 6. Vedi .wslconfig nella guida."
fi

if pactl info >/dev/null 2>&1; then
    ok "Server audio raggiungibile."
else
    problem "Server audio non raggiungibile: la voce delle macchine virtuali non si sentirà."
fi

printf '\n'
if [[ "$PROBLEMS" -eq 0 ]]; then
    printf 'Risultato: la postazione è pronta.\n'
    espeak-ng -v it "La postazione VabaxOS è pronta." 2>/dev/null || true
else
    printf 'Risultato: %d problemi da risolvere.\n' "$PROBLEMS"
    espeak-ng -v it "Ci sono $PROBLEMS problemi da risolvere." 2>/dev/null || true
fi
exit "$PROBLEMS"
