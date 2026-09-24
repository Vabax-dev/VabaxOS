#!/usr/bin/env bash
# Boot test of a VabaxOS ISO in QEMU, without a screen, through the serial console.
#   ./scripts/test-boot.sh [--secure-boot | --bios] [--entry ENTRY] [--timeout SECONDS] [ISO]
# Starts the ISO, waits for the login prompt on the serial console, logs in as
# the live user, reads a few facts about the running system and shuts it down.
# --entry chooses the boot menu entry (ADR-0014):
#   voice     no key pressed: the default entry starts after the timeout
#   novoice   presses N, "VabaxOS senza voce"
#   recovery  presses R, "Modalità di recupero con voce"
# Exit status: 0 if every check passes.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$REPO/out"

MODE=uefi
MODE_OPTION=()
ENTRY=voice
TIMEOUT=300
ISO=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --secure-boot) MODE=secure-boot; MODE_OPTION=(--secure-boot) ;;
        --bios) MODE=bios; MODE_OPTION=(--bios) ;;
        --entry) ENTRY="${2:?--entry vuole voice, novoice o recovery}"; shift ;;
        --timeout) TIMEOUT="${2:?--timeout vuole i secondi}"; shift ;;
        -*) printf 'Uso: %s [--secure-boot | --bios] [--entry voice|novoice|recovery] [--timeout SECONDI] [ISO]\n' "$0" >&2; exit 64 ;;
        *) ISO=("$1") ;;
    esac
    shift
done

# Hotkey of the boot menu entry, and what the kernel command line must contain.
case "$ENTRY" in
    voice) HOTKEY=""; WANT_VOICE=on; WANT_RECOVERY=no ;;
    novoice) HOTKEY=n; WANT_VOICE=off; WANT_RECOVERY=no ;;
    recovery) HOTKEY=r; WANT_VOICE=on; WANT_RECOVERY=yes ;;
    *) printf 'Voce del menu sconosciuta: %s\n' "$ENTRY" >&2; exit 64 ;;
esac

mkdir -p "$OUT/logs"
LOG="$OUT/logs/test-boot-$MODE-$ENTRY-$(date +%Y-%m-%d-%H%M%S).log"
: > "$LOG"
free_port() {
    python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])'
}
# Serial console, and QEMU monitor to press keys in the boot menu.
PORT="$(free_port)"
MONITOR_PORT="$(free_port)"

"$REPO/scripts/run-qemu.sh" --headless --no-audio "${MODE_OPTION[@]}" \
    --serial-tcp "$PORT" "${ISO[@]}" -- -no-reboot \
    -monitor "tcp:127.0.0.1:$MONITOR_PORT,server=on,wait=off" &
QEMU_WRAPPER=$!

# shellcheck disable=SC2317  # called by the EXIT trap
stop_vm() {
    if kill -0 "$QEMU_WRAPPER" 2>/dev/null; then
        pkill -P "$QEMU_WRAPPER" qemu-system 2>/dev/null
        wait "$QEMU_WRAPPER" 2>/dev/null
    fi
}
trap stop_vm EXIT

# Connect to the serial console. QEMU waits for this before starting the VM.
SERIAL=""
for _ in $(seq 50); do
    { exec {SERIAL}<>"/dev/tcp/127.0.0.1/$PORT"; } 2>/dev/null && break
    SERIAL=""
    sleep 0.2
done
[[ -n "$SERIAL" ]] || { printf 'FALLITO: QEMU non è partito.\n'; exit 1; }
cat <&"$SERIAL" >> "$LOG" &

START=$SECONDS
# Waits until the serial log matches a regular expression, or the time runs out.
wait_for() {
    while ! grep -qaE "$1" "$LOG"; do
        if ! kill -0 "$QEMU_WRAPPER" 2>/dev/null; then
            printf 'FALLITO: la macchina virtuale si è fermata prima di: %s\n' "$2"
            return 1
        fi
        if (( SECONDS - START > TIMEOUT )); then
            printf 'FALLITO: dopo %d secondi, ancora niente: %s\n' "$TIMEOUT" "$2"
            return 1
        fi
        sleep 1
    done
}
send() { printf '%s\n' "$1" >&"$SERIAL"; }

printf 'Test di avvio (%s, voce del menu: %s). Log della console seriale: %s\n' "$MODE" "$ENTRY" "$LOG"

# The boot menu gives no sign on the serial console. With UEFI the firmware
# writes a line when it starts GRUB; with BIOS we only count the seconds.
# The key is pressed a few times within the 10 seconds of the menu timeout;
# the kernel command line checked below tells whether it worked.
if [[ -n "$HOTKEY" ]]; then
    if [[ "$MODE" != bios ]]; then
        wait_for 'BdsDxe: starting' 'avvio di GRUB dal firmware' || exit 1
    fi
    sleep 2
    for _ in 1 2 3; do
        { printf 'sendkey %s\n' "$HOTKEY" > "/dev/tcp/127.0.0.1/$MONITOR_PORT"; } 2>/dev/null
        sleep 1
    done
    printf 'INFO: premuto il tasto %s nel menu di avvio.\n' "${HOTKEY^^}"
fi

wait_for 'vabaxos login:' 'richiesta di accesso' || exit 1
printf 'OK: richiesta di accesso sulla console seriale dopo %d secondi.\n' $((SECONDS - START))

send user
wait_for 'Password:' 'richiesta della password' || exit 1
send live
wait_for 'user@vabaxos:~\$' 'prompt della shell' || exit 1
printf 'OK: accesso come utente live.\n'

# The end marker is split so the echoed command line does not match it.
# shellcheck disable=SC2016  # expanded by the shell of the VM, not here
send '[ -d /sys/firmware/efi ] && echo firmware=uefi || echo firmware=bios; f=$(ls /sys/firmware/efi/efivars/SecureBoot-* 2>/dev/null); echo secure-boot=$([ -n "$f" ] && od -An -t u1 "$f" | awk "{print \$NF}" || echo none); echo kernel=$(uname -r); . /etc/os-release; echo "os=$PRETTY_NAME"; echo state=$(timeout 120 systemctl is-system-running --wait); echo voice=$(sed -n "s/.*vabaxos\.voice=\([a-z]*\).*/\1/p" /proc/cmdline); grep -q systemd.unit=multi-user.target /proc/cmdline && echo recovery=yes || echo recovery=no; echo VABAX-""END'
wait_for '^VABAX-END' 'risultato dei controlli' || exit 1
# Each answer is a line "key=value", once terminal control sequences are removed;
# the echoed command line starts with the prompt instead.
value() {
    tr -d '\r' < "$LOG" | sed -e 's/\x1b\[[0-9;?=!]*[A-Za-z]//g' | sed -n "s/^$1=//p" | tail -n 1
}

FAILED=0
check() {
    if [[ "$2" == "$3" ]]; then
        printf 'OK: %s: %s\n' "$1" "$2"
    else
        printf 'FALLITO: %s: %s (atteso: %s)\n' "$1" "$2" "$3"
        FAILED=$((FAILED + 1))
    fi
}
case "$MODE" in
    bios) check firmware "$(value firmware)" bios ;;
    uefi)
        check firmware "$(value firmware)" uefi
        # Without Secure Boot keys the firmware may not create the variable at all.
        SB="$(value secure-boot)"
        [[ "$SB" == none ]] && SB=0
        check 'secure boot' "$SB" 0
        ;;
    secure-boot) check firmware "$(value firmware)" uefi; check 'secure boot' "$(value secure-boot)" 1 ;;
esac
check 'stato di systemd' "$(value state)" running
check 'voce (vabaxos.voice)' "$(value voice)" "$WANT_VOICE"
check 'modalità di recupero' "$(value recovery)" "$WANT_RECOVERY"
printf 'INFO: kernel %s\n' "$(value kernel)"
printf 'INFO: sistema %s\n' "$(value os)"

send 'sudo poweroff'
for _ in $(seq 60); do
    kill -0 "$QEMU_WRAPPER" 2>/dev/null || break
    sleep 1
done
if kill -0 "$QEMU_WRAPPER" 2>/dev/null; then
    printf 'FALLITO: la macchina virtuale non si spegne.\n'
    FAILED=$((FAILED + 1))
else
    printf 'OK: spegnimento.\n'
fi

if [[ "$FAILED" -eq 0 ]]; then
    printf 'Risultato: test di avvio superato (%s, %s).\n' "$MODE" "$ENTRY"
else
    printf 'Risultato: %d controlli falliti (%s, %s).\n' "$FAILED" "$MODE" "$ENTRY"
fi
exit "$FAILED"
