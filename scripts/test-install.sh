#!/usr/bin/env bash
# Installation test of a VabaxOS ISO in QEMU, without a screen (ROADMAP
# v0.1: "the installed system restarts in a VM with speech on").
#   ./scripts/test-install.sh [--keep] [--timeout SECONDS] [ISO]
#
# 1. Installs VabaxOS on a new virtual disk, automatically, with speech on
#    (speakup.synth=soft) and the test answers of
#    image/config/includes.binary/preseed/vabaxos-test.cfg. The installer
#    works on the VM screen (not the serial console) and powers off at the
#    end; 6 processors, because unpacking the system takes long.
# 2. Starts the installed system from the disk and checks it on the
#    serial console, logged in as the test user: VabaxOS packages, live
#    packages removed, console speech heard, welcome at the first start
#    only, speech with no network card.
#
# The disk lives in a temporary folder in out/; --keep keeps it (out/test-install.qcow2).
# Logs go to out/logs/test-install-*.log. Exit status: 0 if every check
# passed, 1 otherwise.
# Commands in single quotes run in the shell of the VM, not here:
# shellcheck disable=SC2016
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$REPO/out"
TIMEOUT=7200
KEEP=false
ISO=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --keep) KEEP=true ;;
        --timeout) TIMEOUT="${2:?--timeout vuole un numero}"; shift ;;
        -*) printf 'Uso: %s [--keep] [--timeout SECONDI] [ISO]\n' "$0" >&2; exit 64 ;;
        *) ISO="$1" ;;
    esac
    shift
done
if [[ -z "$ISO" ]]; then
    shopt -s nullglob
    ISOS=("$OUT"/*.iso)
    shopt -u nullglob
    [[ ${#ISOS[@]} -eq 1 ]] || { printf 'ERRORE: indica la ISO da provare.\n' >&2; exit 64; }
    ISO="${ISOS[0]}"
fi

mkdir -p "$OUT/logs"
STAMP="$(date +%Y-%m-%d-%H%M%S)"
# The virtual disk grows to several GB: in out/, on the real disk, not in
# /tmp, which is often a small tmpfs in memory (WSL).
WORK="$(mktemp -d "$OUT/test-install-work.XXXXXX")"
DISK="$WORK/disk.qcow2"
FAILED=0
QEMU_WRAPPER=""

# shellcheck disable=SC2317  # called by the EXIT trap
cleanup() {
    stop_vm
    if [[ "$KEEP" == true && -f "$DISK" ]]; then
        mv "$DISK" "$OUT/test-install.qcow2"
        printf 'INFO: disco conservato in %s\n' "$OUT/test-install.qcow2"
    fi
    rm -rf "$WORK"
}
# shellcheck disable=SC2317
stop_vm() {
    if [[ -n "$QEMU_WRAPPER" ]] && kill -0 "$QEMU_WRAPPER" 2>/dev/null; then
        pkill -P "$QEMU_WRAPPER" qemu-system 2>/dev/null
        wait "$QEMU_WRAPPER" 2>/dev/null
    fi
    [[ -n "${READER:-}" ]] && kill "$READER" 2>/dev/null
    return 0
}
trap cleanup EXIT

free_port() {
    python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])'
}
check() {
    if [[ "$2" == "$3" ]]; then
        printf 'OK: %s: %s\n' "$1" "$2"
    else
        printf 'FALLITO: %s: %s (atteso: %s)\n' "$1" "$2" "$3"
        FAILED=$((FAILED + 1))
    fi
}

# Starts QEMU with the serial console on a TCP port (QEMU waits for it) and
# the monitor on another. Arguments: log file, run-qemu.sh options, then
# optionally -- and more QEMU options.
start_vm() {
    LOG="$1"
    shift
    local options=() extra=()
    while [[ $# -gt 0 && "$1" != -- ]]; do options+=("$1"); shift; done
    [[ "${1:-}" == -- ]] && shift
    extra=("$@")
    : > "$LOG"
    PORT="$(free_port)"
    MONITOR_PORT="$(free_port)"
    "$REPO/scripts/run-qemu.sh" --headless --serial-tcp "$PORT" "${options[@]}" -- -no-reboot \
        -monitor "tcp:127.0.0.1:$MONITOR_PORT,server=on,wait=off" "${extra[@]}" > "$LOG.qemu" 2>&1 &
    QEMU_WRAPPER=$!
    SERIAL=""
    for _ in $(seq 50); do
        { exec {SERIAL}<>"/dev/tcp/127.0.0.1/$PORT"; } 2>/dev/null && break
        SERIAL=""
        sleep 0.2
    done
    [[ -n "$SERIAL" ]] || { printf 'FALLITO: QEMU non è partito.\n'; exit 1; }
    cat <&"$SERIAL" >> "$LOG" &
    READER=$!
    START=$SECONDS
}
clean_log() {
    tr -d '\r' < "$LOG" | sed -e 's/\x1b\][^\x07\x1b]*\(\x07\|\x1b\\\)//g' -e 's/\x1b\[[0-9;?=!]*[A-Za-z]//g'
}
wait_for() {
    local limit="${3:-$TIMEOUT}"
    while ! clean_log | grep -qaE "$1"; do
        if ! kill -0 "$QEMU_WRAPPER" 2>/dev/null; then
            printf 'FALLITO: la macchina virtuale si è fermata prima di: %s\n' "$2"
            return 1
        fi
        if (( SECONDS - START > limit )); then
            printf 'FALLITO: dopo %d secondi, ancora niente: %s\n' "$limit" "$2"
            return 1
        fi
        sleep 2
    done
}
send() { printf '%s\n' "$1" >&"$SERIAL"; }
monitor() { { printf '%s\n' "$1" > "/dev/tcp/127.0.0.1/$MONITOR_PORT"; } 2>/dev/null; sleep 0.3; }
press() { monitor "sendkey $1"; }
record() {
    local wav="${LOG%.log}-$1.wav"
    monitor "wavcapture $wav snd0"
    sleep "$2"
    monitor "stopcapture 0"
    if python3 "$REPO/scripts/lib/wav-timeline.py" "$wav" 2>/dev/null | grep -q 'voce\|tono'; then
        echo yes
    else
        echo no
    fi
}
ask() {
    local key="$1" command="$2"
    send "echo \"$key\"=\"\$($command)\" ; echo VABAX-\"\"DONE-$key"
    wait_for "^VABAX-DONE-$key" "risposta: $key" 300
}
value() { clean_log | sed -n "s/^$1=//p" | tail -n 1; }
login() {
    wait_for 'login: *$' 'richiesta di accesso' 600 || return 1
    send vabax
    wait_for 'Password: *$' 'richiesta della password' 60 || return 1
    send test
    sleep 3
    send 'export PS1="vabax$ "; export PAGER=cat SYSTEMD_PAGER=cat'
    sleep 1
}

# ---- 1. Automatic installation ------------------------------------------
printf 'Test di installazione di %s\n' "$(basename "$ISO")"
qemu-img create -q -f qcow2 "$DISK" 20G
xorriso -osirrox on -indev "$ISO" -extract /install/gtk/vmlinuz "$WORK/vmlinuz" \
    -extract /install/gtk/initrd.gz "$WORK/initrd.gz" >/dev/null 2>&1 \
    || { printf 'FALLITO: la ISO non contiene l'\''installer grafico.\n'; exit 1; }
LOG="$OUT/logs/test-install-$STAMP-installer.log"
APPEND="auto=true priority=critical preseed/file=/cdrom/preseed/vabaxos-test.cfg"
APPEND+=" locale=en_US.UTF-8 keyboard-configuration/xkb-keymap=us speakup.synth=soft vga=788"
APPEND+=" --- console=ttyS0,115200n8"
start_vm "$LOG" --silent-audio --memory 4096 --cpus 6 --disk "$DISK" "$ISO" -- \
    -kernel "$WORK/vmlinuz" -initrd "$WORK/initrd.gz" -append "$APPEND"
printf 'INFO: installazione in corso (log: %s)\n' "$LOG"
while kill -0 "$QEMU_WRAPPER" 2>/dev/null; do
    if (( SECONDS - START > TIMEOUT )); then
        printf 'FALLITO: installazione non finita dopo %d secondi.\n' "$TIMEOUT"
        exit 1
    fi
    sleep 5
done
stop_vm
INSTALL_TIME=$((SECONDS - START))
if ! qemu-img info "$DISK" | grep -q 'disk size: [0-9.]* GiB'; then
    printf 'FALLITO: il disco è ancora vuoto dopo l'\''installer (vedi %s).\n' "$LOG"
    exit 1
fi
printf 'OK: installazione conclusa in %d secondi.\n' "$INSTALL_TIME"

# ---- 2. First start of the installed system ------------------------------
LOG="$OUT/logs/test-install-$STAMP-first-start.log"
start_vm "$LOG" --silent-audio --memory 4096 --cpus 2 --disk "$DISK" --from-disk
printf 'INFO: primo avvio del sistema installato (log: %s)\n' "$LOG"
wait_for 'login: *$' 'richiesta di accesso sulla console seriale' 600 || exit 1
# The welcome speaks on the first console and waits for keys, like in the
# live system: first answer it, as a user would (language, then start).
check 'benvenuto al primo avvio udibile' "$(record welcome 12)" yes
press ret
sleep 6
press ret
sleep 10
login || exit 1
ask os '. /etc/os-release; echo $PRETTY_NAME'
ask welcome 'systemctl show -p ActiveState --value vabaxos-welcome; test -f /var/lib/vabaxos/welcome-done && echo done'
ask packages 'dpkg-query -W -f "\${Package} " vabaxos-accessibility vabaxos-branding vabaxos-settings vabaxos-setup vabaxos-voice vabaxos-welcome 2>/dev/null | wc -w'
ask live 'dpkg-query -W -f "\${db:Status-Abbrev}\${Package} " live-boot live-config 2>/dev/null | grep -c "^ii" || true'
ask speech 'systemctl is-active espeakup'
ask gdm 'systemctl is-active gdm'
ask voiceselect 'systemctl show -p Result --value vabaxos-voice-select'
ask user 'id -un'
printf 'INFO: sistema %s\n' "$(value os)"
# Diagnosis in the serial log: the welcome, the sound servers and Orca of
# each user, and the login screen.
send 'echo test | sudo -S journalctl -b --no-pager -o short-monotonic -u vabaxos-welcome -u vabaxos-live-audio | tail -20; ps -eo user:12,pid,comm | grep -E "pipewire|wireplumber|orca|espeakup|speech-disp|gdm-"; journalctl -b --no-pager -o cat _COMM=orca | tail -5; ls -la /run/user'
sleep 5
check 'pacchetti VabaxOS installati' "$(value packages)" 6
check 'pacchetti della live rimossi' "$(value live)" 0
check 'voce della console (espeakup)' "$(value speech)" active
check 'schermata di accesso (GDM)' "$(value gdm)" active
check "scelta della voce all'avvio" "$(value voiceselect)" success
check 'benvenuto concluso e segnato' "$(value welcome | tr -s ' ')" "inactive done"
# Orca at the login screen: the greeter must speak without any key.
check 'schermata di accesso udibile' "$(record greeter 12)" yes
press ctrl-alt-f3
check 'voce della console udibile' "$(record console 10)" yes
send 'echo test | sudo -S poweroff'
for _ in $(seq 120); do kill -0 "$QEMU_WRAPPER" 2>/dev/null || break; sleep 1; done
stop_vm

# ---- 3. Second start, with no network: no welcome, speech still on --------
LOG="$OUT/logs/test-install-$STAMP-second-start.log"
start_vm "$LOG" --silent-audio --memory 4096 --cpus 2 --disk "$DISK" --from-disk --no-network
printf 'INFO: secondo avvio, senza rete (log: %s)\n' "$LOG"
login || exit 1
ask welcome2 'systemctl show -p ConditionResult --value vabaxos-welcome'
ask speech2 'systemctl is-active espeakup'
check 'benvenuto non ripetuto' "$(value welcome2)" no
check 'voce della console senza rete' "$(value speech2)" active
press ctrl-alt-f3
check 'voce della console udibile senza rete' "$(record console-offline 10)" yes
send 'echo test | sudo -S poweroff'
for _ in $(seq 120); do kill -0 "$QEMU_WRAPPER" 2>/dev/null || break; sleep 1; done

if [[ $FAILED -eq 0 ]]; then
    printf 'Risultato: test di installazione superato.\n'
    exit 0
fi
printf 'Risultato: %d controlli falliti.\n' "$FAILED"
exit 1
