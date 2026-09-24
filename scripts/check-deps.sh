#!/usr/bin/env bash
# Checks that this machine can build the VabaxOS ISO and start it in QEMU (ADR-0002, ADR-0013).
#   ./scripts/check-deps.sh            check only
#   ./scripts/check-deps.sh --install  as root: install the missing Debian packages (used by the CI)
# Prints one line per check, starting with OK, AVVISO or PROBLEMA.
# Exit status: number of problems found (0 means ready).
set -uo pipefail

# Debian packages needed to build the ISO and to start it in QEMU.
PACKAGES=(
    live-build debootstrap squashfs-tools xorriso mtools dosfstools
    qemu-system-x86 ovmf
    git ca-certificates
)
MIN_FREE_GB=20

INSTALL=false
case "${1:-}" in
    --install) INSTALL=true ;;
    "") ;;
    *)
        printf 'Uso: %s [--install]\n' "$0" >&2
        exit 64
        ;;
esac

PROBLEMS=0
ok() { printf 'OK: %s\n' "$*"; }
warn() { printf 'AVVISO: %s\n' "$*"; }
problem() {
    printf 'PROBLEMA: %s\n' "$*"
    PROBLEMS=$((PROBLEMS + 1))
}

missing_packages() {
    local pkg
    for pkg in "${PACKAGES[@]}"; do
        dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q 'install ok installed' || printf '%s\n' "$pkg"
    done
}

# shellcheck source=/dev/null
. /etc/os-release
if [[ "${VERSION_CODENAME:-}" == trixie ]]; then
    ok "Debian 13 trixie."
else
    problem "Serve Debian 13 trixie, questo sistema è ${PRETTY_NAME:-sconosciuto} (ADR-0002)."
fi

if [[ "$(dpkg --print-architecture 2>/dev/null)" == amd64 ]]; then
    ok "Architettura amd64."
else
    problem "Serve un sistema amd64."
fi

mapfile -t MISSING < <(missing_packages)
if [[ ${#MISSING[@]} -gt 0 && "$INSTALL" == true ]]; then
    if [[ $EUID -ne 0 ]]; then
        problem "--install funziona solo come root."
    else
        printf 'Installo: %s\n' "${MISSING[*]}"
        apt-get update -q && apt-get install -y -q --no-install-recommends "${MISSING[@]}"
        mapfile -t MISSING < <(missing_packages)
    fi
fi
# live-build from forky (ADR-0017), after the Debian 13 packages above.
if [[ "$INSTALL" == true && $EUID -eq 0 ]]; then
    "$(dirname "${BASH_SOURCE[0]}")/install-live-build.sh" || problem "installazione di live-build di forky non riuscita."
fi
if [[ ${#MISSING[@]} -eq 0 ]]; then
    ok "Pacchetti per costruire e avviare la ISO installati."
else
    problem "Mancano questi pacchetti: ${MISSING[*]}. Comando: sudo apt install ${MISSING[*]}"
fi

# Forky images need live-build from forky (ADR-0017).
LB_MIN="1:20250814"
lb_version="$(dpkg-query -W -f='${Version}' live-build 2>/dev/null || true)"
if [[ -n "$lb_version" ]] && dpkg --compare-versions "$lb_version" ge "$LB_MIN"; then
    ok "live-build $lb_version."
elif [[ -n "$lb_version" ]]; then
    problem "live-build $lb_version è troppo vecchio, serve $LB_MIN. Comando: sudo bash scripts/install-live-build.sh"
fi

if [[ $EUID -eq 0 ]]; then
    ok "Eseguito come root: live-build può lavorare."
elif sudo -n /usr/bin/lb --version >/dev/null 2>&1; then
    ok "live-build si avvia con sudo senza password."
else
    warn "sudo chiederà la password per live-build durante la costruzione."
fi

if compgen -G '/usr/share/OVMF/OVMF_CODE_4M*.fd' >/dev/null; then
    ok "Firmware UEFI per QEMU (OVMF) presente."
else
    problem "Firmware OVMF mancante: installa il pacchetto ovmf."
fi

if [[ -r /dev/kvm && -w /dev/kvm ]]; then
    ok "KVM disponibile: QEMU sarà veloce."
else
    warn "KVM non disponibile: QEMU funziona, ma molto più lento."
fi

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FREE_GB=$(df -Pk "$REPO" | awk 'NR==2 {print int($4 / 1048576)}')
if [[ "$FREE_GB" -ge "$MIN_FREE_GB" ]]; then
    ok "Spazio libero: $FREE_GB GB."
else
    problem "Spazio libero: solo $FREE_GB GB. Per costruire la ISO ne servono almeno $MIN_FREE_GB."
fi

if [[ "$PROBLEMS" -eq 0 ]]; then
    printf 'Risultato: tutto pronto.\n'
else
    printf 'Risultato: %d problemi da risolvere.\n' "$PROBLEMS"
fi
exit "$PROBLEMS"
