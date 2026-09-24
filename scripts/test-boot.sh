#!/usr/bin/env bash
# Boot test of a VabaxOS ISO in QEMU, without a screen, through the serial console.
#   ./scripts/test-boot.sh [--secure-boot | --bios] [--entry ENTRY] [--lang it] [--timeout SECONDS] [ISO]
# Starts the ISO, waits for the login prompt on the serial console, logs in as
# the live user, answers the spoken welcome, checks the running system and
# shuts it down. It also records the sound of the VM (QEMU wavcapture) and
# checks that the welcome, console speech and Orca are really heard, or
# silent with "without voice". The recordings stay next to the log.
# --entry chooses the boot menu entry (ADR-0014):
#   voice     no key pressed: the default entry starts after the timeout
#   novoice   presses N, "VabaxOS without voice"
#   recovery  presses R, "Recovery mode with voice" (console only)
#   install   presses I, "Install VabaxOS with voice": checks only that the
#             Debian Installer speaks (no serial console there), then stops
# --lang it chooses Italian in the boot menu first (L, then I).
# Exit status: 0 if every check passes.
# Commands in single quotes run in the shell of the VM, not here:
# shellcheck disable=SC2016
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$REPO/out"

MODE=uefi
MODE_OPTION=()
ENTRY=voice
MENU_LANG=""
TIMEOUT=600
ISO=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --secure-boot) MODE=secure-boot; MODE_OPTION=(--secure-boot) ;;
        --bios) MODE=bios; MODE_OPTION=(--bios) ;;
        --entry) ENTRY="${2:?--entry vuole voice, novoice o recovery}"; shift ;;
        --lang) MENU_LANG="${2:?--lang vuole it}"; shift ;;
        --timeout) TIMEOUT="${2:?--timeout vuole i secondi}"; shift ;;
        -*) printf 'Uso: %s [--secure-boot | --bios] [--entry voice|novoice|recovery] [--lang it] [--timeout SECONDI] [ISO]\n' "$0" >&2; exit 64 ;;
        *) ISO=("$1") ;;
    esac
    shift
done

# For each boot menu entry: hotkey, and what the running system must show.
case "$ENTRY" in
    voice) HOTKEY=""; WANT_VOICE=on; WANT_RECOVERY=no; WANT_SPEECH=active; WANT_DESKTOP=yes; WANT_ORCA=yes; WANT_SOUND=yes ;;
    novoice) HOTKEY=n; WANT_VOICE=off; WANT_RECOVERY=no; WANT_SPEECH=inactive; WANT_DESKTOP=yes; WANT_ORCA=no; WANT_SOUND=no ;;
    recovery) HOTKEY=r; WANT_VOICE=on; WANT_RECOVERY=yes; WANT_SPEECH=active; WANT_DESKTOP=no; WANT_ORCA=no; WANT_SOUND=yes ;;
    install) HOTKEY=i; WANT_SOUND=yes ;;
    *) printf 'Voce del menu sconosciuta: %s\n' "$ENTRY" >&2; exit 64 ;;
esac
case "$MENU_LANG" in
    "") WANT_LANG=en_US.UTF-8 ;;
    it) WANT_LANG=it_IT.UTF-8 ;;
    *) printf 'Lingua non prevista: %s\n' "$MENU_LANG" >&2; exit 64 ;;
esac

mkdir -p "$OUT/logs"
LOG="$OUT/logs/test-boot-$MODE-$ENTRY${MENU_LANG:+-$MENU_LANG}-$(date +%Y-%m-%d-%H%M%S).log"
: > "$LOG"
free_port() {
    python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])'
}
# Serial console, and QEMU monitor to press keys on the screen's keyboard.
PORT="$(free_port)"
MONITOR_PORT="$(free_port)"

# A sound card that plays nothing: the speech services need a card to start.
"$REPO/scripts/run-qemu.sh" --headless --silent-audio "${MODE_OPTION[@]}" \
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
# Sends a command to the QEMU monitor.
monitor() { { printf '%s\n' "$1" > "/dev/tcp/127.0.0.1/$MONITOR_PORT"; } 2>/dev/null; sleep 0.3; }
# Presses a key on the VM keyboard (QEMU key names: ret, n, r, ...).
press() { monitor "sendkey $1"; }
# Records the sound of the VM for SECONDS into <log>-NAME.wav, then prints
# "yes" if there was sound (speech or beeps), "no" if it was silent.
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

# Asks the VM for a value: runs COMMAND in the shell of the VM and waits for
# the line "KEY=<output>". Answers are read with value().
ask() {
    local key="$1" command="$2"
    # The marker is split so the echoed command line does not match it.
    send "echo \"$key\"=\"\$($command)\" ; echo VABAX-\"\"DONE-$key"
    wait_for "^VABAX-DONE-$key" "risposta: $key"
}
# Each answer is a line "key=value", once terminal control sequences are removed:
# CSI sequences (colours, cursor) and OSC sequences, such as the OSC 3008
# context markers that systemd 258 and later write around each command.
# The echoed command line starts with the prompt instead.
value() {
    tr -d '\r' < "$LOG" \
        | sed -e 's/\x1b\][^\x07\x1b]*\(\x07\|\x1b\\\)//g' -e 's/\x1b\[[0-9;?=!]*[A-Za-z]//g' \
        | sed -n "s/^$1=//p" | tail -n 1
}

printf 'Test di avvio (%s, voce del menu: %s). Log della console seriale: %s\n' "$MODE" "$ENTRY" "$LOG"

# The boot menu gives no sign on the serial console. With UEFI the firmware
# writes a line when it starts GRUB; with BIOS we only count the seconds.
# The key is pressed a few times within the 10 seconds of the menu timeout;
# the kernel command line checked below tells whether it worked.
if [[ -n "$HOTKEY" || -n "$MENU_LANG" ]]; then
    if [[ "$MODE" != bios ]]; then
        wait_for 'BdsDxe: starting' 'avvio di GRUB dal firmware' || exit 1
    fi
    sleep 2
    if [[ -n "$MENU_LANG" ]]; then
        # Language submenu, then the language letter; the menu reloads.
        press l
        sleep 1
        press i
        sleep 2
        printf 'INFO: scelta la lingua %s nel menu di avvio (L, I).\n' "$MENU_LANG"
    fi
    if [[ -n "$HOTKEY" ]]; then
        for _ in 1 2 3; do
            press "$HOTKEY"
            sleep 1
        done
        printf 'INFO: premuto il tasto %s nel menu di avvio.\n' "${HOTKEY^^}"
    fi
fi

# The installer has no serial console: record its speech, then stop the VM.
if [[ "$ENTRY" == install ]]; then
    FAILED=0
    sleep 40
    HEARD=no
    for part in 1 2 3; do
        if [[ "$(record "installer-$part" 20)" == yes ]]; then
            HEARD=yes
            break
        fi
    done
    if [[ "$HEARD" == yes ]]; then
        printf 'OK: l'\''installer parla (registrazione %s).\n' "$part"
        printf 'Risultato: test di avvio superato (%s, install).\n' "$MODE"
        exit 0
    fi
    printf 'FALLITO: l'\''installer non parla dopo 100 secondi.\n'
    printf 'Risultato: 1 controlli falliti (%s, install).\n' "$MODE"
    exit 1
fi

wait_for 'vabaxos login:' 'richiesta di accesso' || exit 1
printf 'OK: richiesta di accesso sulla console seriale dopo %d secondi.\n' $((SECONDS - START))

FAILED=0
check() {
    if [[ "$2" == "$3" ]]; then
        printf 'OK: %s: %s\n' "$1" "$2"
    else
        printf 'FALLITO: %s: %s (atteso: %s)\n' "$1" "$2" "$3"
        FAILED=$((FAILED + 1))
    fi
}

# The spoken welcome waits on the first console (ADR-0016). Answer it like a
# person, before logging in on the serial console: a login there would start
# the user's sound server while the welcome still uses the sound card.
# Enter chooses the first language (English), or F1 repeats the message when
# the language came from the boot menu; the welcome then reads the modes,
# which is recorded; Enter again chooses "Try VabaxOS". Not in recovery mode.
if [[ "$WANT_DESKTOP" == yes ]]; then
    sleep 5
    if [[ -z "$MENU_LANG" ]]; then
        press ret
    else
        press f1
    fi
    check 'voce del benvenuto udibile' "$(record welcome 8)" "$WANT_SOUND"
    press ret
    printf 'INFO: risposto al benvenuto (lingua o F1, poi Try VabaxOS).\n'
fi

send user
wait_for 'Password:' 'richiesta della password' || exit 1
send live
wait_for 'user@vabaxos:~\$' 'prompt della shell' || exit 1
printf 'OK: accesso come utente live.\n'

if [[ "$WANT_DESKTOP" == yes ]]; then
    ask welcome 'for i in $(seq 30); do s=$(systemctl show -p ActiveState --value vabaxos-welcome); [ "$s" = activating ] || break; sleep 1; done; echo $s-$(systemctl show -p Result --value vabaxos-welcome)' || exit 1
    check 'benvenuto concluso' "$(value welcome)" inactive-success
fi

ask state 'timeout 180 systemctl is-system-running --wait' || exit 1
ask firmware '[ -d /sys/firmware/efi ] && echo uefi || echo bios' || exit 1
ask secureboot 'f=$(ls /sys/firmware/efi/efivars/SecureBoot-* 2>/dev/null); [ -n "$f" ] && od -An -t u1 "$f" | awk "{print \$NF}" || echo none' || exit 1
ask kernel 'uname -r' || exit 1
ask os '. /etc/os-release; echo $PRETTY_NAME' || exit 1
ask voice 'sed -n "s/.*vabaxos\.voice=\([a-z]*\).*/\1/p" /proc/cmdline' || exit 1
ask recovery 'grep -q systemd.unit=multi-user.target /proc/cmdline && echo yes || echo no' || exit 1
ask speech 'systemctl is-active espeakup' || exit 1
ask lang '. /etc/default/locale; echo $LANG' || exit 1
ask desktop 'for i in $(seq 90); do pgrep -u user -x gnome-shell >/dev/null && break; sleep 1; done; pgrep -u user -x gnome-shell >/dev/null && echo yes || echo no' || exit 1
if [[ "$WANT_ORCA" == yes ]]; then
    ask orca 'for i in $(seq 60); do pgrep -u user -x orca >/dev/null && break; sleep 1; done; pgrep -u user -x orca >/dev/null && echo yes || echo no' || exit 1
else
    ask orca 'sleep 20; pgrep -u user -x orca >/dev/null && echo yes || echo no' || exit 1
fi

case "$MODE" in
    bios) check firmware "$(value firmware)" bios ;;
    uefi)
        check firmware "$(value firmware)" uefi
        # Without Secure Boot keys the firmware may not create the variable at all.
        SB="$(value secureboot)"
        [[ "$SB" == none ]] && SB=0
        check 'secure boot' "$SB" 0
        ;;
    secure-boot) check firmware "$(value firmware)" uefi; check 'secure boot' "$(value secureboot)" 1 ;;
esac
check 'stato di systemd' "$(value state)" running
check 'voce (vabaxos.voice)' "$(value voice)" "$WANT_VOICE"
check 'modalità di recupero' "$(value recovery)" "$WANT_RECOVERY"
check 'voce della console (espeakup)' "$(value speech)" "$WANT_SPEECH"
check 'desktop GNOME' "$(value desktop)" "$WANT_DESKTOP"
check 'Orca' "$(value orca)" "$WANT_ORCA"
check lingua "$(value lang)" "$WANT_LANG"
printf 'INFO: kernel %s\n' "$(value kernel)"
printf 'INFO: sistema %s\n' "$(value os)"

# Sound. In the desktop, a desktop notification must be read by Orca (it is
# read whatever window has the focus). Then the third text console, where
# Speakup must read the login prompt, and back to the desktop (or the first
# console), where Orca must read a new notification.
orca_speaks() {
    send "env DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus gdbus call --session --dest org.freedesktop.Notifications --object-path /org/freedesktop/Notifications --method org.freedesktop.Notifications.Notify VabaxOS 0 '' 'Test $1' 'VabaxOS test' '[]' '{}' 5000 >/dev/null"
    record "$1" 8
}
if [[ "$WANT_DESKTOP" == yes && "$WANT_ORCA" == yes ]]; then
    # Orca speaks through speech-dispatcher, which starts with Orca.
    ask sd 'for i in $(seq 60); do pgrep -u user -x speech-dispatch >/dev/null && break; sleep 1; done; sleep 5; pgrep -u user -x speech-dispatch >/dev/null && echo yes || echo no' || exit 1
fi
if [[ "$WANT_DESKTOP" == yes ]]; then
    check 'Orca udibile nel desktop' "$(orca_speaks orca)" "$WANT_SOUND"
    ask vt 'loginctl show-session $(loginctl list-sessions --no-legend | awk "\$3==\"user\" && \$4==\"seat0\" {print \$1}" | head -1) -p VTNr --value' || exit 1
    BACK_VT="$(value vt)"
else
    BACK_VT=1
fi
press ctrl-alt-f3
check 'voce della console udibile' "$(record console 10)" "$WANT_SOUND"
press "ctrl-alt-f${BACK_VT:-1}"
if [[ "$WANT_DESKTOP" == yes ]]; then
    sleep 3
    check 'Orca udibile al ritorno dalla console' "$(orca_speaks orca-ritorno)" "$WANT_SOUND"
fi

# The first setup opens by itself a few seconds after login: every control
# must have a name for the screen reader (vabaxos-a11y-check, AT-SPI).
BUS='DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus'
if [[ "$WANT_DESKTOP" == yes ]]; then
    ask setupa11y "env $BUS vabaxos-a11y-check --wait 30 vabaxos-setup | tail -1" || exit 1
    check 'configurazione iniziale: comandi senza nome' "$(value setupa11y)" "vabaxos-setup: 0 controls without a name"
fi

# Super+Alt+S turns Orca off and on again (ROADMAP, v0.1).
if [[ "$WANT_ORCA" == yes ]]; then
    press meta_l-alt-s
    ask sroff "sleep 4; env $BUS gsettings get org.gnome.desktop.a11y.applications screen-reader-enabled" || exit 1
    press meta_l-alt-s
    ask sron "sleep 6; env $BUS gsettings get org.gnome.desktop.a11y.applications screen-reader-enabled; pgrep -u user -x orca >/dev/null && echo orca-vivo" || exit 1
    check 'Super+Alt+S spegne Orca' "$(value sroff)" false
    check 'Super+Alt+S riaccende Orca' "$(value sron)" true
fi

# Mouse keys crashed GNOME Shell on Wayland in GNOME 48 (mutter #4008).
if [[ "$WANT_DESKTOP" == yes ]]; then
    ask mousekeys "p=\$(pgrep -u user -x gnome-shell); env $BUS gsettings set org.gnome.desktop.a11y.keyboard mousekeys-enable true; sleep 6; q=\$(pgrep -u user -x gnome-shell); env $BUS gsettings set org.gnome.desktop.a11y.keyboard mousekeys-enable false; [ -n \"\$q\" ] && [ \"\$p\" = \"\$q\" ] && echo stabile || echo crash" || exit 1
    check 'tasti del mouse: GNOME Shell' "$(value mousekeys)" stabile
fi

if [[ "$(value state)" != running ]]; then
    ask failed 'systemctl --failed --no-legend --plain | cut -d" " -f1 | paste -sd,' || exit 1
    printf 'INFO: unità fallite: %s\n' "$(value failed)"
fi

# During shutdown systemd logs to the kernel log, which reaches the serial
# console: the log then tells which service slows the shutdown down, if any.
send 'sudo dmesg -n 7; sudo systemd-analyze log-target kmsg; sudo systemd-analyze log-level info; sudo poweroff'
SHUTDOWN_START=$SECONDS
for _ in $(seq 120); do
    kill -0 "$QEMU_WRAPPER" 2>/dev/null || break
    sleep 1
done
SHUTDOWN_SECONDS=$((SECONDS - SHUTDOWN_START))
if kill -0 "$QEMU_WRAPPER" 2>/dev/null; then
    printf 'FALLITO: la macchina virtuale non si spegne in 2 minuti.\n'
    FAILED=$((FAILED + 1))
elif (( SHUTDOWN_SECONDS > 30 )); then
    printf 'FALLITO: spegnimento lento, %d secondi.\n' "$SHUTDOWN_SECONDS"
    FAILED=$((FAILED + 1))
else
    printf 'OK: spegnimento in %d secondi.\n' "$SHUTDOWN_SECONDS"
fi
SLOW="$(tr -d '\r' < "$LOG" | sed -n 's/.*systemd\[1\]: \([^:]*\): State .stop-sigterm. timed out.*/\1/p' | sort -u | paste -sd,)"
[[ -z "$SLOW" ]] || printf 'INFO: servizi lenti a fermarsi: %s\n' "$SLOW"

if [[ "$FAILED" -eq 0 ]]; then
    printf 'Risultato: test di avvio superato (%s, %s%s).\n' "$MODE" "$ENTRY" "${MENU_LANG:+, $MENU_LANG}"
else
    printf 'Risultato: %d controlli falliti (%s, %s%s).\n' "$FAILED" "$MODE" "$ENTRY" "${MENU_LANG:+, $MENU_LANG}"
fi
exit "$FAILED"
