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
#   welcome-install  no key pressed; in the welcome: English, Install VabaxOS,
#             Install now (ADR-0023): the live system must restart into the
#             installer with kexec, without the firmware, and it must speak
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
        -*) printf 'Uso: %s [--secure-boot | --bios] [--entry voice|novoice|recovery|install|welcome-install] [--lang it] [--timeout SECONDI] [ISO]\n' "$0" >&2; exit 64 ;;
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
    welcome-install) HOTKEY=""; WANT_SOUND=yes ;;
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

# shellcheck disable=SC2317,SC2329  # called by the EXIT trap
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
# Waits until the serial log matches a regular expression, or TIMEOUT
# seconds pass. Each wait has its own time: counting from the start of the
# test, every answer that was not there at once failed after 600 seconds
# (the tests with the voice last about 10 minutes; 2026-09-26).
wait_for() {
    local end=$((SECONDS + TIMEOUT))
    while ! grep -qaE "$1" "$LOG"; do
        if ! kill -0 "$QEMU_WRAPPER" 2>/dev/null; then
            printf 'FALLITO: la macchina virtuale si è fermata prima di: %s\n' "$2"
            return 1
        fi
        if (( SECONDS > end )); then
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
# ask, but waits at most SECONDS and returns 1 without a failure: for
# answers the VM may never give (after a suspend).
ask_within() {
    local seconds="$1" key="$2" command="$3" end=$((SECONDS + $1))
    send "echo \"$key\"=\"\$($command)\" ; echo VABAX-\"\"DONE-$key"
    while ! grep -qaE "^VABAX-DONE-$key" "$LOG"; do
        (( SECONDS < end )) || return 1
        kill -0 "$QEMU_WRAPPER" 2>/dev/null || return 1
        sleep 1
    done
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

# The installer has no serial console: record its speech, up to a minute.
installer_speaks() {
    local part
    for part in 1 2 3; do
        if [[ "$(record "installer-$part" 20)" == yes ]]; then
            printf 'OK: l'\''installer parla (registrazione %s).\n' "$part"
            return 0
        fi
    done
    printf 'FALLITO: l'\''installer non parla dopo 100 secondi.\n'
    return 1
}
if [[ "$ENTRY" == install ]]; then
    sleep 40
    if installer_speaks; then
        printf 'Risultato: test di avvio superato (%s, install).\n' "$MODE"
        exit 0
    fi
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

# Install from the welcome (ADR-0023): English, Install VabaxOS, Install now.
# The live system restarts into the installer with kexec: with UEFI, one
# more "BdsDxe: starting" from the firmware would mean a normal restart.
if [[ "$ENTRY" == welcome-install ]]; then
    FIRMWARE_STARTS="$(grep -ac 'BdsDxe: starting' "$LOG")"
    sleep 5
    press ret
    check 'voce del benvenuto udibile' "$(record welcome 8)" yes
    press down
    sleep 2
    press ret
    sleep 5
    press ret
    printf 'INFO: nel benvenuto: Install VabaxOS, poi Install now.\n'
    sleep 40
    if [[ "$MODE" != bios ]]; then
        check 'riavvio senza firmware (kexec)' "$(( $(grep -ac 'BdsDxe: starting' "$LOG") - FIRMWARE_STARTS ))" 0
    fi
    installer_speaks || FAILED=$((FAILED + 1))
    if [[ "$FAILED" -eq 0 ]]; then
        printf 'Risultato: test di avvio superato (%s, welcome-install).\n' "$MODE"
        exit 0
    fi
    printf 'Risultato: %d controlli falliti (%s, welcome-install).\n' "$FAILED" "$MODE"
    exit 1
fi

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
ask logo '. /etc/os-release; echo $LOGO' || exit 1
ask voice 'sed -n "s/.*vabaxos\.voice=\([a-z]*\).*/\1/p" /proc/cmdline' || exit 1
ask recovery 'grep -q systemd.unit=multi-user.target /proc/cmdline && echo yes || echo no' || exit 1
ask speech 'systemctl is-active espeakup' || exit 1
ask firewall 'echo $(systemctl is-active ufw) $(vabaxos-status firewall)' || exit 1
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
# ADR-0021: ufw on, in every mode; vabaxos-status says it.
check 'firewall attivo' "$(value firewall | sed 's/Firewall attivo\./Firewall on./')" 'active Firewall on.'
check 'desktop GNOME' "$(value desktop)" "$WANT_DESKTOP"
check 'Orca' "$(value orca)" "$WANT_ORCA"
check lingua "$(value lang)" "$WANT_LANG"
printf 'INFO: kernel %s\n' "$(value kernel)"
printf 'INFO: sistema %s\n' "$(value os)"
check 'nome e logo VabaxOS' "$(value logo)" vabaxos-logo

# Sound. In the desktop, a desktop notification must be read by Orca (it is
# read whatever window has the focus). Then the third text console, where
# Speakup must read the login prompt, and back to the desktop (or the first
# console), where Orca must read a new notification.
# The test notification is closed after listening: GNOME Shell keeps a
# banner on screen while the user is idle, and the accessibility checks
# that follow would find its buttons (the expand and close buttons of
# GNOME Shell 50 have no name) instead of the Start menu alone.
NOTIFY="env DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus gdbus call --session --dest org.freedesktop.Notifications --object-path /org/freedesktop/Notifications --method org.freedesktop.Notifications"
orca_speaks() {
    # gdbus prints "(uint32 ID,)".
    send "n=\$($NOTIFY.Notify VabaxOS 0 '' 'Test $1' 'VabaxOS test' '[]' '{}' 5000 | awk '{print \$2+0}')"
    record "$1" 8
    send "$NOTIFY.CloseNotification \"\$n\" >/dev/null"
}
# Orca's state, when it has to be heard and is not, or after it restarts:
# whether it runs, how often systemd restarted it (its watchdog, 30
# seconds in VabaxOS, kills Orca when its main loop waits longer, for
# example on speech-dispatcher), the watchdog kills and the speech
# processes. Details to the serial log (ORCA-DIAG), a summary as INFO.
orca_state() {
    send 'journalctl --user -b --no-pager -o short-monotonic -u orca | grep -E "Start|watchdog|Killing|Failed" | tail -12 | sed "s/^/ORCA-DIAG: /"; pgrep -u user -a -f "speech-dispatch|sd_[a-z]" | sed "s/^/ORCA-DIAG: /"'
    ask orcastate 'echo $(systemctl --user show orca -p ActiveState -p SubState -p NRestarts --value) watchdog=$(journalctl --user -b --no-pager -o cat -u orca | grep -c "result .watchdog.")' || exit 1
    printf 'INFO: Orca %s: %s\n' "$1" "$(value orcastate)"
    # Who is silent: speech-dispatcher said directly (without Orca), and
    # the sound server's outputs and streams.
    send 'wpctl status 2>&1 | sed -n "/Audio/,/Video/p" | sed "s/^/ORCA-DIAG: /"; journalctl --user -b --no-pager -o cat -u orca | tail -15 | sed "s/^/ORCA-DIAG: /"; grep -a -E "Incoming text|Queueing|Audio|rror|[Ss]top|[Pp]ause|END|BEGIN|Terminating|started" /run/user/1000/speech-dispatcher/log/speech-dispatcher.log | tail -n 60 | cut -c1-200 | sed "s/^/SPEECHD-DIAG: /"; tail -n 30 /run/user/1000/speech-dispatcher/log/espeak-ng.log | cut -c1-200 2>&1 | sed "s/^/SPEECHD-DIAG: /"; spd-say -w "VabaxOS test" >/dev/null 2>&1 &'
    printf 'INFO: speech-dispatcher da solo %s: %s\n' "$1" "$(record "spd-$2" 5)"
    # Below speech-dispatcher (CI of block 15, 2026-09-26: even spd-say was
    # silent, until a suspend and resume): a sound played straight on
    # PipeWire, whether the sound card still moves (hw_ptr grows while
    # RUNNING) and the sound server's own log.
    send 'for i in 1 2; do grep -E "^(state|hw_ptr)" /proc/asound/card0/pcm0p/sub0/status | tr "\n" " " | sed "s/^/AUDIO-DIAG: /"; echo; sleep 1; done; pactl list sink-inputs short 2>&1 | sed "s/^/AUDIO-DIAG: /"; journalctl --user -b --no-pager -o short-monotonic -u pipewire -u wireplumber -u pipewire-pulse | tail -12 | cut -c1-220 | sed "s/^/AUDIO-DIAG: /"; pw-play /usr/share/sounds/vabaxos/stereo/complete.oga >/dev/null 2>&1 &'
    printf 'INFO: suono diretto su PipeWire %s: %s\n' "$1" "$(record "pw-$2" 5)"
}
# Whether speech-dispatcher is heard at this point of the test (INFO only):
# to find after which step the sound stops, when Orca is silent later.
speech_probe() {
    [[ "$WANT_ORCA" == yes ]] || return 0
    ask "probetime$2" 'date +%T' || exit 1
    send 'spd-say -w "VabaxOS test" >/dev/null 2>&1 &'
    printf 'INFO: voce udibile %s (%s): %s\n' "$1" "$(value "probetime$2")" "$(record "probe-$2" 4)"
}
if [[ "$WANT_DESKTOP" == yes && "$WANT_ORCA" == yes ]]; then
    # Orca speaks through speech-dispatcher, which starts with Orca.
    ask sd 'for i in $(seq 60); do pgrep -u user -x speech-dispatch >/dev/null && break; sleep 1; done; sleep 5; pgrep -u user -x speech-dispatch >/dev/null && echo yes || echo no' || exit 1
fi
if [[ "$WANT_DESKTOP" == yes ]]; then
    ORCA_HEARD="$(orca_speaks orca)"
    check 'Orca udibile nel desktop' "$ORCA_HEARD" "$WANT_SOUND"
    # Orca silent: GNOME Shell's and Orca's messages go to the serial log,
    # to see whether the desktop is stuck (CI, 2026-09-25: GNOME Shell did
    # not answer on the session bus from the start in one run of eight).
    if [[ "$ORCA_HEARD" != "$WANT_SOUND" ]]; then
        # Also: busy or waiting? The threads of GNOME Shell and their CPU use
        # over 3 seconds, where its main thread waits in the kernel, and the
        # whole journal. One line: typing after sudo would reach sudo.
        send 'sudo -n journalctl -b --no-pager -o short-monotonic _COMM=gnome-shell _COMM=orca | tail -80 | sed "s/^/JOURNAL: /"; p=$(pgrep -u user -x gnome-shell); top -b -H -n 2 -d 3 -p "$p" | tail -20 | sed "s/^/SHELLTOP: /"; sudo -n cat /proc/"$p"/stack | sed "s/^/SHELLSTACK: /"; sudo -n journalctl -b --no-pager -o short-monotonic --since=-3min | grep -v -e speech-disp -e sd_espeak -e sd_kokoro -e sudo | tail -120 | sed "s/^/JOURNALALL: /"'
        ask diagnosis 'echo done' || exit 1
        # Where each thread of GNOME Shell waits: gdb from the network, with
        # the symbols from debuginfod.debian.net (only when Orca is silent;
        # to find the cause of the freeze at startup, 2026-09-26).
        send 'sudo apt-get update -qq >/dev/null 2>&1; sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq gdb >/dev/null 2>&1; sudo env DEBUGINFOD_URLS=https://debuginfod.debian.net timeout 900 gdb -p "$(pgrep -u user -x gnome-shell)" -batch -ex "set debuginfod enabled on" -ex "set pagination off" -ex "thread apply all bt 40" -ex "call (void)gjs_dumpstack()" 2>&1 | grep -v -e "^\\[New LWP" -e "^Reading" -e "^Download" | sed "s/^/GDB: /"; journalctl --user -b --no-pager -o cat _COMM=gnome-shell | tail -40 | sed "s/^/GJS: /"; echo GDB""END'
        TIMEOUT=1200 wait_for '^GDBEND' 'gdb' || exit 1
    fi
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

# Desktop voice (ADR-0019, ADR-0024): the service must succeed and write
# eSpeak NG as the default module. Then Kokoro is chosen the way a user
# does in vabaxos-setup (Orca's synthesizer): the module must load the
# model in advance and Orca must still speak.
if [[ "$WANT_DESKTOP" == yes ]]; then
    ask voiceselect 'systemctl show -p Result --value vabaxos-voice-select' || exit 1
    ask voicemodule 'sed -n "s/^DefaultModule //p" /etc/speech-dispatcher/clients/zz-vabaxos-voice.conf' || exit 1
    ask voicereason 'grep "^#" /var/lib/vabaxos/voice.conf | tr -d "#"' || exit 1
    check "scelta della voce all'avvio" "$(value voiceselect)" success
    check 'voce predefinita del desktop (eSpeak NG)' "$(value voicemodule)" espeak-ng
    printf 'INFO: voce del desktop: %s (%s)\n' "$(value voicemodule)" "$(value voicereason)"
fi
if [[ "$WANT_DESKTOP" == yes && "$WANT_ORCA" == yes ]]; then
    ask forcekokoro "env $BUS gsettings set org.gnome.Orca.Speech:/org/gnome/orca/default/speech/ synthesizer kokoro; pkill -u user -x speech-dispatch; env $BUS gsettings set org.gnome.desktop.a11y.applications screen-reader-enabled false; sleep 2; env $BUS gsettings set org.gnome.desktop.a11y.applications screen-reader-enabled true; echo fatto" || exit 1
    ask orcaback 'for i in $(seq 60); do pgrep -u user -x orca >/dev/null && break; sleep 1; done; sleep 15; pgrep -u user -x orca >/dev/null && echo yes || echo no' || exit 1
    # The module loads the model in the background when Orca uses Kokoro
    # (about 570 MB): wait for it, up to 2 minutes on slow machines
    # such as the CI runners, then Orca must speak with it.
    ask kokoro 'for i in $(seq 120); do r=$(ps -o rss= -C sd_kokoro | sort -n | tail -1); [ "${r:-0}" -gt 300000 ] && break; sleep 1; done; [ "${r:-0}" -gt 300000 ] && echo yes || echo "no (${r:-0} kB)"' || exit 1
    check 'Orca udibile con Kokoro' "$(orca_speaks orca-kokoro)" "$WANT_SOUND"
    check 'voce naturale Kokoro caricata' "$(value kokoro)" yes
    # Back to the default voice (ADR-0024) for the rest of the test: the
    # checks after this one test what a user has at first.
    # speech-dispatcher's detailed log from here on (LogLevel 5, set back
    # to 3 after the web test): if the sound stops later, SPEECHD-DIAG shows
    # what it received and what its modules answered.
    ask backespeak "sudo -n sed -i 's/^#* *LogLevel .*/LogLevel 5/' /etc/speech-dispatcher/speechd.conf; env $BUS gsettings reset org.gnome.Orca.Speech:/org/gnome/orca/default/speech/ synthesizer; pkill -u user -x speech-dispatch; env $BUS gsettings set org.gnome.desktop.a11y.applications screen-reader-enabled false; sleep 2; env $BUS gsettings set org.gnome.desktop.a11y.applications screen-reader-enabled true; for i in \$(seq 60); do pgrep -u user -x orca >/dev/null && break; sleep 1; done; sleep 15; echo fatto" || exit 1
    orca_state 'dopo il ritorno a eSpeak NG' ritorno
fi

# GNOME Shell for Orca: the taskbar with the Start button and the search
# box (block 15, ADR-0025: the VabaxOS Start menu for everyone, ArcMenu
# removed) and every control with a name. The full accessibility tree of
# GNOME Shell goes to the serial log, to see what the screen reader finds.
# A notification is on screen during the check (critical, so its banner
# stays until it is closed): GNOME Shell 50 draws its Close and Expand
# buttons with an icon only, and button-names@vabaxos.org must give them a
# name (ADR-0022).
if [[ "$WANT_DESKTOP" == yes ]]; then
    ask arcmenu "env $BUS gnome-extensions list --enabled | grep -c arcmenu@arcmenu.com" || exit 1
    check 'ArcMenu tolto' "$(value arcmenu)" 0
    ask buttonnames "env $BUS gnome-extensions list --enabled --active | grep -c button-names@vabaxos.org" || exit 1
    check 'nomi dei pulsanti di GNOME Shell attivi' "$(value buttonnames)" 1
    send "n=\$($NOTIFY.Notify VabaxOS 0 '' 'Test menu' 'VabaxOS test' '[]' '{\"urgency\": <byte 2>}' 0 | awk '{print \$2+0}')"
    sleep 3
    send "env $BUS vabaxos-a11y-check --list gnome-shell > /tmp/shell-a11y.txt 2>&1; sed 's/^/A11Y: /' /tmp/shell-a11y.txt"
    ask shella11y "tail -1 /tmp/shell-a11y.txt" || exit 1
    ask bannernames "grep -A12 'notification:' /tmp/shell-a11y.txt | grep -c -E 'button: (Close|Chiudi)\$'" || exit 1
    ask taskbarstart "grep -c -E 'button: Start\$' /tmp/shell-a11y.txt" || exit 1
    ask taskbarsearch "grep -c -E '(entry|text): (Search programs, settings and files|Cerca programmi, impostazioni e file)\$' /tmp/shell-a11y.txt" || exit 1
    send "$NOTIFY.CloseNotification \"\$n\" >/dev/null"
    check 'GNOME Shell: comandi senza nome' "$(value shella11y)" "gnome-shell: 0 controls without a name"
    check 'pulsante Start sulla barra' "$([[ "$(value taskbarstart)" =~ ^[1-9] ]] && echo yes || echo no)" yes
    check 'casella di ricerca sulla barra' "$([[ "$(value taskbarsearch)" =~ ^[1-9] ]] && echo yes || echo no)" yes
    printf 'INFO: pulsanti Chiudi nelle notifiche: %s\n' "$(value bannernames)"
    speech_probe 'dopo la notifica e le estensioni' shell
fi

# Desktop programs (block 5, ROADMAP v0.1): Files, Terminal and the
# Settings panels for Wi-Fi, Bluetooth and Power must open, and the
# controls without a name are counted. GNOME programs are not ours: the
# counts are information, with the full trees in the serial log.
# GNOME Settings starts only when XDG_CURRENT_DESKTOP says GNOME.
DESKTOP_ENV="$BUS WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 XDG_CURRENT_DESKTOP=GNOME"
app_a11y() {
    local key="$1" launch="$2" name="$3"
    send "env $DESKTOP_ENV $launch >/dev/null 2>&1 &"
    ask "$key" "env $BUS vabaxos-a11y-check --wait 40 $name > /tmp/$key.txt 2>&1; tail -1 /tmp/$key.txt" || exit 1
    send "sed 's/^/A11Y-$key: /' /tmp/$key.txt | grep 'NO NAME' ; pkill -f '$launch' ; sleep 2"
    printf 'INFO: %s\n' "$(value "$key")"
}
if [[ "$WANT_DESKTOP" == yes ]]; then
    app_a11y files nautilus nautilus
    app_a11y terminal ptyxis ptyxis
    # GNOME Settings is on the accessibility bus as gnome-control-center
    # (not "settings", as on the session bus: org.gnome.Settings).
    app_a11y wifi 'gnome-control-center wifi' gnome-control-center
    app_a11y bluetooth 'gnome-control-center bluetooth' gnome-control-center
    app_a11y power 'gnome-control-center power' gnome-control-center
    speech_probe 'dopo File, Terminale e Impostazioni' settings
    ask status "env $BUS vabaxos-status battery" || exit 1
    printf 'INFO: vabaxos-status: %s\n' "$(value status)"
    ask soundtheme "env $BUS gsettings get org.gnome.desktop.sound theme-name" || exit 1
    check 'tema dei suoni' "$(value soundtheme)" "'vabaxos'"
    ask font "env $BUS gsettings get org.gnome.desktop.interface font-name" || exit 1
    check 'font del desktop' "$(value font)" "'Atkinson Hyperlegible Next 11'"
fi

# The complete system (block 7): office and e-mail open and their
# unnamed controls are counted; Braille, text recognition and the help
# are ready.
if [[ "$WANT_DESKTOP" == yes ]]; then
    app_a11y writer 'libreoffice --writer' soffice
    app_a11y mail thunderbird thunderbird
    ask braille 'test -s /etc/brlapi.key && command -v brltty >/dev/null && python3 -c "import brlapi" && echo pronto' || exit 1
    check 'Braille (brltty, BrlAPI)' "$(value braille)" pronto
    ask ocr 'tesseract --list-langs 2>/dev/null | grep -c "^ita$"' || exit 1
    check 'riconoscimento del testo in italiano' "$(value ocr)" 1
    ask help 'ls /usr/share/doc/vabaxos-help/html/*.html | wc -l' || exit 1
    printf 'INFO: pagine dell'"'"'aiuto: %s\n' "$(value help)"
    speech_probe 'dopo Writer e Thunderbird' office
fi

# A familiar interface (block 8): the extensions are active (the check of
# GNOME Shell above also covers the taskbar, since it reads all of it),
# windows have Minimize and Maximize, Ctrl+Shift+Esc opens the System
# Monitor, and the Programs window has a name on every control.
if [[ "$WANT_DESKTOP" == yes ]]; then
    ask extensions "env $BUS gnome-extensions list --enabled --active | grep -c -E 'dash-to-panel|ubuntu-appindicators|ding@|GPaste|tiling-assistant|vabaxos-keys|button-names'" || exit 1
    check 'estensioni attive (barra, icone, appunti, finestre, tasti e menu Start, nomi dei pulsanti)' "$(value extensions)" 7
    ask buttons "env $BUS gsettings get org.gnome.desktop.wm.preferences button-layout" || exit 1
    check 'pulsanti delle finestre' "$(value buttons)" "'appmenu:minimize,maximize,close'"
    press ctrl-shift-esc
    ask taskmanager 'for i in $(seq 20); do pgrep -u user -x gnome-system-mo >/dev/null && break; sleep 1; done; pgrep -u user -x gnome-system-mo >/dev/null && echo yes || echo no' || exit 1
    check 'Ctrl+Maiusc+Esc apre il Monitor di sistema' "$(value taskmanager)" yes
    send 'pkill -u user -x gnome-system-mo'
    app_a11y programs vabaxos-apps vabaxos-apps
    speech_probe 'dopo Monitor di sistema e Programmi' programs
fi

# The keys of Windows (block 8): Super+T and Super+B move the focus to the
# taskbar and to the notification area (what Orca would read there is in
# the log), copy, cut and paste work in a program, Alt+F4 closes a window
# and on the desktop asks to shut down (then Escape).
focus_after() {
    local key="$1"
    press "$2"
    sleep 2
    ask "$key" "env $BUS vabaxos-a11y-check --focused gnome-shell" || exit 1
    press esc
    sleep 1
}
if [[ "$WANT_DESKTOP" == yes ]]; then
    ask keys "echo \$(env $BUS gsettings get org.gnome.shell.keybindings toggle-quick-settings) \$(env $BUS gsettings get org.gnome.desktop.wm.keybindings switch-windows)" || exit 1
    check 'tasti di Windows (Super+A, Alt+Tab)' "$(value keys)" "['<Super>a'] ['<Alt>Tab']"
    # The Programs window has just closed: the window under it (Writer, with
    # its first welcome) takes the focus a moment later, and would take it
    # back from the taskbar (seen in QEMU: 2 seconds fail, 5 are enough).
    sleep 5
    focus_after taskbar meta_l-t
    check 'Super+T porta il focus sulla barra delle applicazioni' "$(value taskbar | grep -c 'focus: push button\|focus: button')" 1
    printf 'INFO: Super+T: %s\n' "$(value taskbar)"
    # What vabaxos-keys did with it (its line in the journal), and any
    # error of GNOME Shell's JavaScript.
    ask supertlog "sudo -n journalctl -b --no-pager -o cat _COMM=gnome-shell | grep -E 'vabaxos-keys: Super\\+T|JS ERROR' | tail -3 | paste -sd'|'" || exit 1
    printf 'INFO: Super+T in GNOME Shell: %s\n' "$(value supertlog)"
    # Desktop Icons NG kills and starts again its desktop program when its
    # window does not appear within 3 seconds: on a slow machine (QEMU
    # without KVM) it starts again every 3 seconds, forever.
    ask dinglaunch 'sudo -n journalctl -b --no-pager -o cat _COMM=gnome-shell | grep -c "Launching DING process"' || exit 1
    printf 'INFO: avvii del desktop (DING): %s\n' "$(value dinglaunch)"
    focus_after tray meta_l-b
    check "Super+B porta il focus sull'area di notifica" "$(value tray | grep -vc 'focus: none\|Main stage')" 1
    printf 'INFO: Super+B: %s\n' "$(value tray)"
    # The text is counted, not the lines: Text Editor pastes on the same
    # line (its last newline is not part of the text).
    send "printf 'VabaxOS copia\n' > /tmp/copia.txt; env $DESKTOP_ENV gnome-text-editor --standalone /tmp/copia.txt >/dev/null 2>&1 &"
    ask editor "env $BUS vabaxos-a11y-check --wait 40 --focused gnome-text-editor" || exit 1
    sleep 3
    printf 'INFO: editor di testo: %s\n' "$(value editor)"
    press ctrl-a; press ctrl-c; press ctrl-end; press ctrl-v; press ctrl-s
    sleep 2
    ask copied 'grep -o "VabaxOS copia" /tmp/copia.txt | wc -l' || exit 1
    check 'Ctrl+C e Ctrl+V: testo copiato e incollato' "$(value copied)" 2
    press ctrl-a; press ctrl-x; press ctrl-s
    sleep 2
    ask cut 'grep -o "VabaxOS copia" /tmp/copia.txt | wc -l' || exit 1
    press ctrl-v; press ctrl-s
    sleep 2
    ask pasted 'grep -o "VabaxOS copia" /tmp/copia.txt | wc -l' || exit 1
    check 'Ctrl+X taglia e Ctrl+V incolla di nuovo' "$(value cut) $(value pasted)" "0 2"
    press alt-f4
    ask closed 'sleep 3; pgrep -u user -x gnome-text-edit >/dev/null && echo aperto || echo chiuso' || exit 1
    check 'Alt+F4 chiude la finestra' "$(value closed)" chiuso
    # Close every window first (the first setup opens by itself at login):
    # with a window left, Alt+F4 closes it, as in Windows.
    # ask, not send: Alt+F4 must wait until the windows are closed.
    ask closedall 'pkill -u user -x gnome-text-edit; pkill -u user -f vabaxos-setup; pkill -u user -f soffice; pkill -u user -x thunderbird; sleep 3; echo done' || exit 1
    press alt-f4
    sleep 3
    ask poweroff "env $BUS vabaxos-a11y-check --focused gnome-shell" || exit 1
    # Seen once with Orca (2026-09-25), not reproduced by hand: the first
    # Alt+F4 did nothing. A second try is allowed, and said in the log.
    if [[ "$(value poweroff | grep -ci 'power off\|restart\|cancel')" != 1 ]]; then
        printf 'INFO: Alt+F4 sul desktop: il primo non ha aperto la richiesta, riprovo\n'
        press alt-f4
        sleep 3
        ask poweroff2 "env $BUS vabaxos-a11y-check --focused gnome-shell" || exit 1
        [[ "$(value poweroff2 | grep -ci 'power off\|restart\|cancel')" == 1 ]] && ask poweroff "echo \"$(value poweroff2)\"" >/dev/null
    fi
    press esc
    printf 'INFO: Alt+F4 sul desktop: %s\n' "$(value poweroff)"
    check 'Alt+F4 sul desktop chiede di spegnere' "$(value poweroff | grep -ci 'power off\|restart\|cancel')" 1
    speech_probe 'dopo i tasti di Windows e Alt+F4' keys
fi

# Screen reader settings (block 9): every control of the window has a name,
# and a change reaches the running Orca at once through its D-Bus service
# (the speed read back from Orca itself).
if [[ "$WANT_DESKTOP" == yes ]]; then
    app_a11y screenreader vabaxos-screen-reader vabaxos-screen-reader
fi
if [[ "$WANT_ORCA" == yes ]]; then
    ask orcaset "env $BUS vabaxos-screen-reader --set voices/default rate 63" || exit 1
    check 'impostazione di Orca applicata subito' "$(value orcaset)" 'saved, applied at once'
    ask orcarate "env $BUS vabaxos-screen-reader --status | sed -n 's/^rate: //p'" || exit 1
    check 'velocità letta da Orca (D-Bus)' "$(value orcarate)" 63
    ask orcadconf "env $BUS gsettings get org.gnome.Orca.Voice:/org/gnome/orca/default/voices/default/ rate" || exit 1
    check 'velocità salvata nelle impostazioni' "$(value orcadconf)" 63
    speech_probe 'dopo le impostazioni del lettore di schermo' screenreader
fi

# Orca's keys (block 10): the NVDA scheme is the default, with Insert as
# the screen reader key (not Caps Lock: Orca 50 does not hold it back under
# Wayland), and Orca answers to it: Insert+F12 says the time (recorded).
if [[ "$WANT_DESKTOP" == yes ]]; then
    ask orcakeys "env $BUS gsettings get org.gnome.Orca.Keybindings:/org/gnome/orca/default/keybindings/ entries | grep -o \"'sayAllHandler': \[\['Down', '461', '256', '1'\]\]\" | wc -l" || exit 1
    check 'tasti di Orca come NVDA (Ins+Freccia giù legge tutto)' "$(value orcakeys)" 1
    ask orcamod "env $BUS gsettings get org.gnome.Orca.Keybindings:/org/gnome/orca/default/keybindings/ desktop-modifier-keys" || exit 1
    check 'tasto del lettore di schermo (Ins, come in NVDA)' "$(value orcamod)" "['Insert', 'KP_Insert']"
fi
if [[ "$WANT_ORCA" == yes ]]; then
    sleep 3
    press insert-f12
    HEARD="$(record orca-f12 5)"
    check 'Ins+F12: Orca dice l'"'"'ora' "$HEARD" "$WANT_SOUND"
    [[ "$HEARD" == "$WANT_SOUND" ]] || orca_state 'dopo Ins+F12' f12
    # Orca runs without DISPLAY (orca.service.d/50-vabaxos-wayland.conf):
    # no xkbcomp through Xwayland, which froze GNOME Shell at startup.
    ask orcadisplay 'tr "\\0" "\\n" < /proc/$(pgrep -u user -x orca)/environ | grep -c "^DISPLAY="' || exit 1
    check 'Orca senza DISPLAY (niente xkbcomp)' "$(value orcadisplay)" 0
fi

# Navigation and Tab (block 11). Tab is pressed many times in a program
# while vabaxos-a11y-check listens to where the focus goes, as Orca hears
# it: the stops go to the serial log (TAB-key), the summary is checked for
# the VabaxOS programs (no stop without a name, the focus never leaves the
# program, Tab moves) and shown for the others.
tab_walk() {
    local key="$1" launch="$2" name="$3" presses="${4:-20}" seconds
    seconds=$((presses + 12))
    send "env $DESKTOP_ENV $launch >/dev/null 2>&1 &"
    # "open$key", not "${key}open": ask waits for the line VABAX-DONE-<key>,
    # and VABAX-DONE-tabappsopen would already answer for tabapps.
    ask "open$key" "timeout 60 env $BUS vabaxos-a11y-check --wait 40 --focused $name" || exit 1
    send "timeout $((seconds + 30)) env $BUS vabaxos-a11y-check --watch-focus $seconds $name > /tmp/tab-$key.txt 2>&1 &"
    sleep 4
    for _ in $(seq "$presses"); do
        press tab
        sleep 0.5
    done
    # Wait for the summary: pressing Tab through QEMU takes longer than
    # the presses themselves.
    ask "$key" "for i in \$(seq 60); do grep -q ' tab: stops=' /tmp/tab-$key.txt && break; sleep 1; done; tail -1 /tmp/tab-$key.txt" || exit 1
    send "sed 's/^/TAB-$key: /' /tmp/tab-$key.txt; pkill -f '$launch'; sleep 2"
}
# The numbers of a summary "stops=.. unique=.. controls=.. unnamed=.. outside=..".
tab_value() { value "$1" | sed -n "s/.* $2=\([0-9]*\).*/\1/p"; }
if [[ "$WANT_ORCA" == yes ]]; then
    send 'pkill -u user -f vabaxos-setup; sleep 2'
    for program in "apps|vabaxos-apps|vabaxos-apps" "screenreader|vabaxos-screen-reader|vabaxos-screen-reader"; do
        IFS='|' read -r key launch name <<< "$program"
        tab_walk "tab$key" "$launch" "$name"
        printf 'INFO: Tab in %s: %s\n' "$name" "$(value "tab$key")"
        check "Tab in $name: fermate senza nome" "$(tab_value "tab$key" unnamed)" 0
        check "Tab in $name: il focus resta nel programma" "$(tab_value "tab$key" outside)" 0
        check "Tab in $name: il focus si sposta" "$( (( $(tab_value "tab$key" unique) > 3 )) && echo yes || echo no)" yes
    done
    # Other programs: only reported. Not the editors (text editor, Writer):
    # there Tab writes a tab in the text.
    for program in "files|nautilus|nautilus" "settings|gnome-control-center wifi|gnome-control-center"; do
        IFS='|' read -r key launch name <<< "$program"
        tab_walk "tab$key" "$launch" "$name"
        printf 'INFO: Tab in %s: %s\n' "$name" "$(value "tab$key")"
    done
fi

# A new window takes the focus even when a program already has it and the
# new one has no activation token (started from here): no "is ready".
# Super+Alt+D says where the focus is.
if [[ "$WANT_DESKTOP" == yes ]]; then
    send "printf 'VabaxOS\\n' > /tmp/nuova.txt; env $DESKTOP_ENV gnome-text-editor --standalone /tmp/nuova.txt >/dev/null 2>&1 &"
    ask firstwindow "env $BUS vabaxos-a11y-check --wait 40 --focused gnome-text-editor" || exit 1
    send "env $DESKTOP_ENV vabaxos-apps >/dev/null 2>&1 &"
    ask newwindow "sleep 8; env $BUS vabaxos-a11y-check --wait 30 --focused vabaxos-apps" || exit 1
    check 'la finestra nuova prende il focus' "$(value newwindow | grep -c 'focus: none')" 0
    printf 'INFO: finestra nuova: %s\n' "$(value newwindow)"
    if [[ "$WANT_ORCA" == yes ]]; then
        press meta_l-alt-d
        # Orca may start speaking after 3 seconds: record 10.
        HEARD="$(record where-am-i 10)"
        check 'Super+Alt+D: dove sono (Orca)' "$HEARD" "$WANT_SOUND"
        [[ "$HEARD" == "$WANT_SOUND" ]] || orca_state 'dopo Super+Alt+D' where
    fi
    send 'pkill -u user -x vabaxos-apps; pkill -u user -x gnome-text-edit; sleep 2'
fi

# The VabaxOS Start menu (block 12, ADR-0025 proposed): Super opens it with
# the focus in the search field, results arrive while writing, Tab goes to
# the categories, Right Arrow opens one; every control has a name.
if [[ "$WANT_DESKTOP" == yes ]]; then
    ask startrunning 'for i in $(seq 30); do pgrep -u user -f "vabaxos-start" >/dev/null && break; sleep 1; done; pgrep -u user -f "vabaxos-start" >/dev/null && echo yes || echo no' || exit 1
    check 'menu Start pronto in memoria' "$(value startrunning)" yes
    press meta_l
    ask startsearch "sleep 2; env $BUS vabaxos-a11y-check --wait 20 --focused vabaxos-start" || exit 1
    check 'Super apre il menu Start nella ricerca' "$(value startsearch | grep -c 'focus: text\|focus: entry')" 1
    for letter in f i l e; do press "$letter"; done
    ask startresults "sleep 2; env $BUS vabaxos-a11y-check --list vabaxos-start | grep -c 'list item\|row'" || exit 1
    printf 'INFO: risultati della ricerca «file»: %s\n' "$(value startresults)"
    press esc
    press tab
    ask starttree "sleep 1; env $BUS vabaxos-a11y-check --focused vabaxos-start" || exit 1
    printf 'INFO: Tab nel menu Start: %s\n' "$(value starttree)"
    check 'Tab va alle categorie' "$(value starttree | grep -c 'focus: none\|focus: text')" 0
    # Tab stops on the first category, Favorites: P jumps to Programs, then
    # Right Arrow opens it and shows its groups (Office, Internet...).
    press p
    press right
    ask startopen "sleep 1; env $BUS vabaxos-a11y-check --list vabaxos-start | grep -c 'Office\|Ufficio\|Internet'" || exit 1
    groups="$(value startopen)"
    printf 'INFO: dopo P e Freccia destra: %s gruppi di Programmi\n' "${groups:-0}"
    check 'P e Freccia destra aprono Programmi' "$(( ${groups:-0} > 0 ))" 1
    ask startnames "env $BUS vabaxos-a11y-check vabaxos-start | tail -1" || exit 1
    check 'menu Start: comandi senza nome' "$(value startnames)" 'vabaxos-start: 0 controls without a name'
    press esc
    press esc
fi

# The web with Orca (block 14): Firefox opens the practice page of the
# help, and the quick keys of NVDA read its content, not only the roles
# (the GNOME 50 problem of Orca reading only labels in Firefox). What Orca
# says is read from speech-dispatcher's log (LogLevel 5: "Incoming text"),
# which needs a new speech-dispatcher: Orca connects again by itself.
if [[ "$WANT_DESKTOP" == yes && "$WANT_ORCA" == yes ]]; then
    SPEECHD_LOG=/run/user/1000/speech-dispatcher/log/speech-dispatcher.log
    ask weblog "sudo -n sed -i 's/^#* *LogLevel .*/LogLevel 5/' /etc/speech-dispatcher/speechd.conf; pkill -u user -x speech-dispatch; echo ok" || exit 1
    send "env $DESKTOP_ENV firefox-esr /usr/share/doc/vabaxos-help/html/prova-web.html >/dev/null 2>&1 &"
    ask webopen "for i in \$(seq 90); do env $BUS vabaxos-a11y-check --focused Firefox 2>/dev/null | grep -q 'document web: Pagina di prova' && break; sleep 2; done; env $BUS vabaxos-a11y-check --focused Firefox" || exit 1
    check 'Firefox apre la pagina di prova con il focus' "$(value webopen | grep -c 'document web: Pagina di prova per Orca')" 1
    ask webmark "sleep 5; grep -ac '' $SPEECHD_LOG" || exit 1
    # Ctrl+Home first: Firefox may start with the caret on a link of the
    # navigation (CI, 2026-09-26). Then H twice: the first heading has the
    # text of the window title, which Orca also says when the window opens;
    # the second is only in the page.
    for key in ctrl-home h h k d t; do
        press "$key"
        sleep 4
    done
    ask webspeech "sleep 4; tail -n +$(value webmark) $SPEECHD_LOG | grep -a 'Incoming text' | sed 's/.*Incoming text: |//; s/|\$//; s/<[^>]*>//g' | tr '\\n' '/'" || exit 1
    printf 'INFO: Orca nella pagina di prova (Ctrl+Inizio, H, H, K, D, T): %s\n' "$(value webspeech)"
    check 'Orca legge il titolo con H' "$(value webspeech | grep -c 'Titoli')" 1
    check 'Orca legge il collegamento con K' "$(value webspeech | grep -c 'vai al modulo')" 1
    check 'Orca legge la tabella con T' "$(value webspeech | grep -c 'Orari della biblioteca')" 1
    check 'H e K non ripetono la lettera premuta' "$(value webspeech | grep -cE '(^|/)[hk]/')" 0
    ask webnames "env $BUS vabaxos-a11y-check Firefox | tail -1" || exit 1
    printf 'INFO: Firefox: %s\n' "$(value webnames)"
    # ask, not send: typing ahead after sudo would reach sudo.
    ask webclose "pkill -u user firefox; sudo -n sed -i 's/^LogLevel 5/LogLevel 3/' /etc/speech-dispatcher/speechd.conf; sleep 3; echo ok" || exit 1
fi

# Suspend and resume (ROADMAP v0.1): after waking up, Orca must speak.
if [[ "$WANT_DESKTOP" == yes && "$WANT_ORCA" == yes ]]; then
    send 'sudo systemctl suspend </dev/null'
    sleep 15
    # Entering the suspend can take longer than 15 seconds (CI, 2026-09-26:
    # the wake-up came first, then the machine went to sleep for good): wake
    # it up again until the kernel logs "PM: suspend exit". A wake-up while
    # it runs does nothing. The live user may not read the system journal:
    # sudo (without it the count was always 0, 2026-09-26).
    # In QEMU the suspend sometimes stops half-way after a long test (the
    # kernel still echoes the keys, the shell does not answer; 2026-09-25,
    # not reproduced by hand): a known defect, to check on a physical PC
    # (ROADMAP v0.1: suspend works, or the defect is documented).
    # One key for each try: ask waits for the line VABAX-DONE-<key>.
    resumed=0
    for try in 1 2 3 4; do
        monitor system_wakeup
        sleep 10
        ask_within 120 "resumed$try" 'sudo -n journalctl -k -b --no-pager -o cat | grep -c "PM: suspend exit"' || break
        resumed="$(value "resumed$try")"
        [[ "$resumed" -gt 0 ]] && break
    done
    if [[ "$resumed" -eq 0 ]]; then
        printf 'INFO: la macchina virtuale non torna dalla sospensione (difetto noto in QEMU, da provare su PC fisico)\n'
        # If the shell still answers: where the suspend stopped.
        if ask_within 60 suspendlog 'echo "$(systemctl show -p ActiveState --value systemd-suspend.service) | $(sudo -n journalctl -b --no-pager -o short-monotonic -u systemd-suspend.service -u systemd-logind.service | tail -6 | cut -c1-150 | paste -sd"|")"'; then
            printf 'INFO: stato della sospensione: %s\n' "$(value suspendlog)"
        fi
        stop_vm
        if [[ "$FAILED" -eq 0 ]]; then
            printf 'Risultato: test di avvio superato (%s, %s%s), senza la prova dello spegnimento.\n' "$MODE" "$ENTRY" "${MENU_LANG:+, $MENU_LANG}"
        else
            printf 'Risultato: %d controlli falliti (%s, %s%s).\n' "$FAILED" "$MODE" "$ENTRY" "${MENU_LANG:+, $MENU_LANG}"
        fi
        exit "$FAILED"
    fi
    ask sleepstate 'cat /sys/power/state; journalctl -b --no-pager -o cat -u systemd-suspend.service | tail -1' || exit 1
    printf 'INFO: sospensione riuscita %s volte; stati: %s\n' "$resumed" "$(value sleepstate)"
    HEARD="$(orca_speaks orca-resume)"
    check 'Orca udibile dopo la sospensione' "$HEARD" "$WANT_SOUND"
    [[ "$HEARD" == "$WANT_SOUND" ]] || orca_state 'dopo la sospensione' resume
fi

if [[ "$(value state)" != running ]]; then
    ask failed 'systemctl --failed --no-legend --plain | cut -d" " -f1 | paste -sd,' || exit 1
    printf 'INFO: unità fallite: %s\n' "$(value failed)"
fi

# During shutdown systemd logs to the kernel log, which reaches the serial
# console: the log then tells which service slows the shutdown down, if any.
# The shutdown sound (vabaxos-shutdown-sound.service) plays after the user
# sessions stop, in every mode: the recording runs until the VM is off.
SHUTDOWN_WAV="${LOG%.log}-shutdown.wav"
monitor "wavcapture $SHUTDOWN_WAV snd0"
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
if python3 "$REPO/scripts/lib/wav-timeline.py" "$SHUTDOWN_WAV" 2>/dev/null | grep -q 'voce\|tono'; then
    check 'suono di spegnimento udibile' yes yes
else
    check 'suono di spegnimento udibile' no yes
fi
SLOW="$(tr -d '\r' < "$LOG" | sed -n 's/.*systemd\[1\]: \([^:]*\): State .stop-sigterm. timed out.*/\1/p' | sort -u | paste -sd,)"
[[ -z "$SLOW" ]] || printf 'INFO: servizi lenti a fermarsi: %s\n' "$SLOW"

if [[ "$FAILED" -eq 0 ]]; then
    printf 'Risultato: test di avvio superato (%s, %s%s).\n' "$MODE" "$ENTRY" "${MENU_LANG:+, $MENU_LANG}"
else
    printf 'Risultato: %d controlli falliti (%s, %s%s).\n' "$FAILED" "$MODE" "$ENTRY" "${MENU_LANG:+, $MENU_LANG}"
fi
exit "$FAILED"
