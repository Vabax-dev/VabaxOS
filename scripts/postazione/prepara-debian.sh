#!/usr/bin/env bash
# Prepares Debian on WSL2 as the VabaxOS development workstation (ADR-0013).
# Run it as your normal user, not as root:
#   bash /mnt/c/VabaxOS-postazione/prepara-debian.sh
# Every message is plain text, one line each, so it reads well with a screen reader.
set -euo pipefail

REPO_URL="https://github.com/Vabax-dev/VabaxOS.git"
DEST="$HOME/projects/VabaxOS"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_LIST="$HERE/pacchetti-debian.txt"

step() { printf '\n== %s\n' "$*"; }
ok() { printf 'OK: %s\n' "$*"; }
problem() { printf 'PROBLEMA: %s\n' "$*"; }
ask_yes() {
    local answer
    read -r -p "$1 Scrivi s per si, n per no, poi Invio: " answer
    [[ "$answer" == [sSyY]* ]]
}

if [[ "$(id -u)" -eq 0 ]]; then
    problem "Non eseguire questo script come root. Eseguilo come il tuo utente normale."
    exit 1
fi

if [[ ! -f "$PKG_LIST" ]]; then
    problem "Non trovo l'elenco dei pacchetti: $PKG_LIST"
    exit 1
fi

IS_WSL=false
if grep -qi microsoft /proc/version 2>/dev/null; then
    IS_WSL=true
fi

step "Passo 1 di 8: controllo della versione di Debian"
# shellcheck source=/dev/null
. /etc/os-release
case "${VERSION_CODENAME:-}" in
    trixie)
        ok "Debian 13 trixie."
        ;;
    bookworm)
        printf 'Questa è Debian 12 bookworm. VabaxOS si sviluppa su Debian 13 trixie.\n'
        if ! ask_yes "Aggiorno Debian a trixie adesso? Ci vogliono alcuni minuti."; then
            problem "Aggiornamento rifiutato. Lo script si ferma qui."
            exit 1
        fi
        printf 'Ti verrà chiesta la password di Debian. Mentre la scrivi non si sente niente: è normale.\n'
        sudo find /etc/apt -name '*.list' -o -name '*.sources' | while read -r f; do
            sudo sed -i 's/bookworm/trixie/g' "$f"
        done
        sudo apt-get update
        sudo DEBIAN_FRONTEND=noninteractive apt-get full-upgrade -y
        ok "Debian aggiornata a trixie."
        ;;
    *)
        problem "Versione di Debian non prevista: ${PRETTY_NAME:-sconosciuta}. Serve Debian 13 trixie."
        exit 1
        ;;
esac

step "Passo 2 di 8: installazione dei pacchetti"
printf 'Ti verrà chiesta la password di Debian. Mentre la scrivi non si sente niente: è normale.\n'
mapfile -t PACKAGES < <(grep -Ev '^[[:space:]]*(#|$)' "$PKG_LIST")
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${PACKAGES[@]}"
ok "Installati ${#PACKAGES[@]} pacchetti."

step "Passo 3 di 8: accesso alla virtualizzazione (KVM) per QEMU"
if ! getent group kvm >/dev/null; then
    sudo groupadd --system kvm
fi
sudo usermod -aG kvm "$USER"
ok "Utente $USER aggiunto al gruppo kvm."
if $IS_WSL; then
    KVM_COMMAND='command = "chgrp kvm /dev/kvm; chmod 660 /dev/kvm"'
    if [[ ! -f /etc/wsl.conf ]] || ! grep -q '^\[boot\]' /etc/wsl.conf; then
        printf '\n[boot]\n%s\n' "$KVM_COMMAND" | sudo tee -a /etc/wsl.conf >/dev/null
        ok "Permessi di /dev/kvm impostati a ogni avvio di WSL."
    elif grep -q 'dev/kvm' /etc/wsl.conf; then
        ok "Permessi di /dev/kvm già configurati in /etc/wsl.conf."
    elif sed -n '/^\[boot\]/,/^\[/p' /etc/wsl.conf | grep -q '^command'; then
        problem "In /etc/wsl.conf c'è già un comando di avvio. Aggiungi a mano: chgrp kvm /dev/kvm; chmod 660 /dev/kvm"
    else
        sudo sed -i "/^\[boot\]/a $KVM_COMMAND" /etc/wsl.conf
        ok "Permessi di /dev/kvm impostati a ogni avvio di WSL."
    fi
fi

step "Passo 4 di 8: permesso di costruire la ISO senza password"
printf 'live-build deve lavorare come amministratore. Se accetti, il comando lb potrà essere eseguito\n'
printf 'con sudo senza chiedere la password, così Claude può costruire la ISO da solo.\n'
printf 'Vuol dire che dentro questa Debian Claude avrà di fatto i poteri di amministratore.\n'
printf 'Windows e i tuoi file restano protetti dai normali permessi del tuo utente Windows.\n'
if ask_yes "Concedo il permesso?"; then
    SUDOERS_TMP="$(mktemp)"
    printf '%s ALL=(root) NOPASSWD: /usr/bin/lb\n' "$USER" >"$SUDOERS_TMP"
    if sudo visudo -cf "$SUDOERS_TMP" >/dev/null; then
        sudo install -m 0440 "$SUDOERS_TMP" /etc/sudoers.d/vabaxos-live-build
        ok "Permesso concesso solo per il comando lb."
    else
        problem "Regola sudo non valida, non la installo."
    fi
    rm -f "$SUDOERS_TMP"
else
    ok "Permesso non concesso. Quando serve costruire la ISO, Claude ti chiederà di eseguire il comando."
fi

step "Passo 5 di 8: identità per i commit"
if git config --global user.name >/dev/null && git config --global user.email >/dev/null; then
    ok "Git usa già il nome $(git config --global user.name) e l'email $(git config --global user.email)."
else
    read -r -p "Nome da usare nei commit, per esempio Vabax: " GIT_NAME
    read -r -p "Email da usare nei commit: " GIT_EMAIL
    git config --global user.name "$GIT_NAME"
    git config --global user.email "$GIT_EMAIL"
    ok "Identità dei commit impostata."
fi
git config --global init.defaultBranch main
git config --global pull.ff only

step "Passo 6 di 8: copia del repository VabaxOS"
mkdir -p "$HOME/projects"
if [[ -d "$DEST/.git" ]]; then
    git -C "$DEST" pull --ff-only
    ok "Repository già presente in $DEST, aggiornato."
else
    git clone "$REPO_URL" "$DEST"
    ok "Repository copiato in $DEST."
fi

step "Passo 7 di 8: prova della voce"
if espeak-ng -v it "La postazione VabaxOS sta parlando." 2>/dev/null; then
    ok "Se hai sentito la frase, l'audio di WSL funziona."
else
    problem "espeak-ng non è riuscito a parlare. Lo controlleremo con la verifica dopo il riavvio."
fi

step "Passo 8 di 8: riavvio di WSL"
printf 'Le modifiche ai gruppi e a /etc/wsl.conf valgono dopo un riavvio di WSL.\n'
printf 'Dopo il riavvio riapri Debian dal menu Start ed esegui la verifica:\n'
printf '  bash ~/projects/VabaxOS/scripts/postazione/verifica-postazione.sh\n'
if $IS_WSL && command -v wsl.exe >/dev/null; then
    read -r -p "Premi Invio per chiudere WSL. Questa finestra si chiuderà. " _
    wsl.exe --shutdown
else
    printf 'Chiudi questa finestra, poi in PowerShell esegui: wsl --shutdown\n'
fi
