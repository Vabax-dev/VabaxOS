#!/usr/bin/env bash
# Upgrade test: from an installed VabaxOS to the next version, in QEMU,
# as a user does it (ADR-0020, ADR-0028).
#   ./scripts/test-upgrade.sh [--keep] [--timeout SECONDS] [DISK]
#
# DISK is an installed VabaxOS (default out/test-install.qcow2, left by
# scripts/test-install.sh --keep): today the ISO of this branch, after the
# 0.1 the disk installed from the ISO of the 0.1. The test never changes it:
# the VM writes on a copy-on-write layer.
#
# 1. Builds the VabaxOS packages of this checkout with a higher version
#    (VABAXOS_VERSION=<next>+upgradetest), in an APT archive signed with a
#    throwaway key (scripts/build-archive.sh), served to the VM over HTTP.
# 2. Starts the installed system, writes a setting of Orca as the user
#    does, adds the archive to APT and updates with vabaxos-update --now
#    (PackageKit, the same way as Aggiorna VabaxOS). Debian's sources stay
#    as they are: new dependencies and today's security updates come too.
# 3. Checks: every VabaxOS package at the new version, nothing half
#    installed or broken, no configuration file left aside (.dpkg-dist),
#    the diversion of Orca's start kept, the user's settings kept, the
#    welcome not back, automatic security updates set up (two origins).
# 4. Starts again from the disk: login screen and console speech heard,
#    before the serial login (as in test-install.sh), Orca's setting and
#    the services after the restart.
#
# Logs go to out/logs/test-upgrade-*.log. Exit status: 0 if every check
# passed, 1 otherwise.
# Commands in single quotes run in the shell of the VM, not here:
# shellcheck disable=SC2016
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$REPO/out"
TIMEOUT=3600
KEEP=false
BASE="$OUT/test-install.qcow2"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --keep) KEEP=true ;;
        --timeout) TIMEOUT="${2:?--timeout vuole un numero}"; shift ;;
        -*) printf 'Uso: %s [--keep] [--timeout SECONDI] [DISCO]\n' "$0" >&2; exit 64 ;;
        *) BASE="$1" ;;
    esac
    shift
done
[[ -f "$BASE" ]] || { printf 'ERRORE: manca il disco installato %s (scripts/test-install.sh --keep).\n' "$BASE" >&2; exit 64; }
BASE="$(cd "$(dirname "$BASE")" && pwd)/$(basename "$BASE")"

mkdir -p "$OUT/logs"
STAMP="$(date +%Y-%m-%d-%H%M%S)"
WORK="$(mktemp -d "$OUT/test-upgrade-work.XXXXXX")"
DISK="$WORK/disk.qcow2"
FAILED=0
QEMU_WRAPPER=""
HTTP=""

# shellcheck disable=SC2317,SC2329  # called by the EXIT trap
cleanup() {
    stop_vm
    [[ -n "$HTTP" ]] && kill "$HTTP" 2>/dev/null
    if [[ "$KEEP" == true && -f "$DISK" ]]; then
        mv "$DISK" "$OUT/test-upgrade.qcow2"
        printf 'INFO: disco aggiornato conservato in %s (sopra %s)\n' "$OUT/test-upgrade.qcow2" "$BASE"
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
start_vm() {
    LOG="$1"
    shift
    : > "$LOG"
    PORT="$(free_port)"
    MONITOR_PORT="$(free_port)"
    "$REPO/scripts/run-qemu.sh" --headless --serial-tcp "$PORT" "$@" -- -no-reboot \
        -monitor "tcp:127.0.0.1:$MONITOR_PORT,server=on,wait=off" > "$LOG.qemu" 2>&1 &
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
}
clean_log() {
    tr -d '\r' < "$LOG" | sed -e 's/\x1b\][^\x07\x1b]*\(\x07\|\x1b\\\)//g' -e 's/\x1b\[[0-9;?=!]*[A-Za-z]//g'
}
wait_for() {
    local limit="${3:-$TIMEOUT}"
    local end=$((SECONDS + limit))
    while ! clean_log | grep -qaE "$1"; do
        if ! kill -0 "$QEMU_WRAPPER" 2>/dev/null; then
            printf 'FALLITO: la macchina virtuale si è fermata prima di: %s\n' "$2"
            return 1
        fi
        if (( SECONDS > end )); then
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
# One command, one answer line; the limit in seconds is optional.
ask() {
    local key="$1" command="$2"
    send "echo \"$key\"=\"\$($command)\" ; echo VABAX-\"\"DONE-$key"
    wait_for "^VABAX-DONE-$key" "risposta: $key" "${3:-300}"
}
value() { clean_log | sed -n "s/^$1=//p" | tail -n 1; }
login() {
    wait_for 'login: *$' 'richiesta di accesso' 600 || return 1
    send vabax
    wait_for 'Password: *$' 'richiesta della password' 60 || return 1
    send test
    sleep 3
    send 'export PS1="vabax$ "; export PAGER=cat SYSTEMD_PAGER=cat XDG_RUNTIME_DIR=/run/user/$(id -u)'
    sleep 1
}
# Everything with sudo on one line: words typed after a sudo can end up in
# sudo's password prompt (CLAUDE.md).
as_root() { printf 'echo test | sudo -S sh -c %q 2>/dev/null' "$1"; }
power_off() {
    send 'echo test | sudo -S poweroff'
    for _ in $(seq 120); do kill -0 "$QEMU_WRAPPER" 2>/dev/null || break; sleep 1; done
    stop_vm
}

ORCA_RATE="python3 -c 'import json, os; print(json.load(open(os.path.expanduser(\"~/.local/share/orca/user-settings.conf\")))[\"profiles\"][\"default\"][\"voices\"][\"default\"][\"rate\"])'"
VABAXOS_PACKAGES="dpkg-query -W -f '\${db:Status-Abbrev}\${Package}\n' 'vabaxos-*' 2>/dev/null | sed -n 's/^ii *//p'"

# ---- 1. The next version, in a signed archive -----------------------------
# shellcheck source=/dev/null
. "$REPO/image/build.conf"
NEXT="${VABAXOS_NEXT_VERSION}+upgradetest"
NEXT_DEB="${NEXT//-/\~}"
printf 'Test di aggiornamento: %s -> %s\n' "$(basename "$BASE")" "$NEXT_DEB"
VABAXOS_VERSION="$NEXT" "$REPO/scripts/build-packages.sh" "$WORK/debs" >/dev/null 2>"$WORK/build.log" \
    || { cat "$WORK/build.log"; printf 'FALLITO: pacchetti della versione nuova.\n'; exit 1; }
export GNUPGHOME="$WORK/gnupg"
mkdir -m 0700 "$GNUPGHOME"
gpg --batch --quiet --passphrase '' --quick-generate-key "VabaxOS upgrade test key" ed25519 sign 1d
gpg --batch --armor --export "VabaxOS upgrade test key" > "$WORK/key.asc"
VABAXOS_ARCHIVE_KEY="$(gpg --batch --armor --export-secret-keys "VabaxOS upgrade test key")" \
    VABAXOS_ARCHIVE_PUBLIC_KEY="$WORK/key.asc" VABAXOS_ARCHIVE_DEBS="$WORK/debs" \
    GNUPGHOME="$WORK/unused" "$REPO/scripts/build-archive.sh" "$WORK/site" \
    || { printf 'FALLITO: archivio della versione nuova.\n'; exit 1; }
# package=version of each package of the archive, for the check after.
EXPECTED="$(find "$WORK/site/pool" -name '*.deb' -exec dpkg-deb -f {} Package Version \; \
    | paste -d' ' - - | sed 's/^Package: \(.*\) Version: \(.*\)$/\1=\2/' | tr '\n' ' ')"
HTTP_PORT="$(free_port)"
python3 -m http.server --bind 127.0.0.1 --directory "$WORK/site" "$HTTP_PORT" >/dev/null 2>&1 &
HTTP=$!
# QEMU's user network: the host is 10.0.2.2 for the VM.
ARCHIVE_URL="http://10.0.2.2:$HTTP_PORT/"

qemu-img create -q -f qcow2 -b "$BASE" -F qcow2 "$DISK"

# ---- 2. The installed system, updated as a user does it -------------------
LOG="$OUT/logs/test-upgrade-$STAMP-update.log"
start_vm "$LOG" --silent-audio --memory 4096 --cpus 2 --disk "$DISK" --from-disk
printf 'INFO: aggiornamento (log: %s)\n' "$LOG"
login || exit 1
ask before "$VABAXOS_PACKAGES | while read -r p; do printf '%s=%s ' \$p \$(dpkg-query -W -f '\${Version}' \$p); done"
printf 'INFO: prima: %s\n' "$(value before)"
# A setting of Orca, as the user writes it with the screen reader settings.
ask orcaset 'vabaxos-screen-reader --set voices/default rate 63'
ask ratebefore "$ORCA_RATE"
check 'impostazione di Orca scritta prima di aggiornare' "$(value ratebefore)" 63
ask welcomebefore "$(as_root 'test -f /var/lib/vabaxos/welcome-done && echo done')"
# The archive of the next version, with its key, as vabaxos-apt writes it.
ask source "$(as_root "python3 -c 'import urllib.request, sys; sys.stdout.buffer.write(urllib.request.urlopen(sys.argv[1]).read())' ${ARCHIVE_URL}vabaxos-archive.asc > /usr/share/keyrings/vabaxos-upgrade-test.asc && printf 'Types: deb\nURIs: $ARCHIVE_URL\nSuites: vabaxos\nComponents: main debian-fixes\nSigned-By: /usr/share/keyrings/vabaxos-upgrade-test.asc\n' > /etc/apt/sources.list.d/zz-vabaxos-upgrade-test.sources && echo ready")"
check "archivio della versione nuova aggiunto" "$(value source)" ready
# Aggiorna VabaxOS: PackageKit, the new sources first. As root: polkit
# lets root update without a password prompt (on the desktop GNOME asks it).
send "$(as_root 'vabaxos-update --now; echo UPDATE-EXIT=$?')"
wait_for '^UPDATE-EXIT=' 'fine di vabaxos-update --now' "$TIMEOUT" || exit 1
check 'vabaxos-update --now concluso' "$(clean_log | sed -n 's/^UPDATE-EXIT=//p' | tail -n 1)" 0
clean_log | grep -aE '^(Update finished|The update stopped|[0-9]+ updates)' | sed 's/^/INFO: /'

# Every installed package that the archive has must be at its version there.
ask old "for pv in $EXPECTED; do p=\${pv%%=*}; v=\${pv#*=}; s=\$(dpkg-query -W -f '\${db:Status-Abbrev}\${Version}' \$p 2>/dev/null); case \"\$s\" in 'ii '*) [ \"\${s#ii }\" = \"\$v\" ] || printf '%s ' \"\$p:\${s#ii }\" ;; esac; done"
check 'ogni pacchetto VabaxOS alla versione nuova' "$(value old | sed 's/ *$//')" ""
ask audit "$(as_root 'dpkg --audit | wc -l')"
check 'nessun pacchetto installato a metà (dpkg --audit)' "$(value audit)" 0
ask aptcheck "$(as_root 'apt-get check -q >/dev/null 2>&1 && echo ok')"
check 'dipendenze a posto (apt-get check)' "$(value aptcheck)" ok
ask leftover "$(as_root "find /etc -name '*.dpkg-dist' -o -name '*.dpkg-new' -o -name '*.ucf-dist' | wc -l")"
check 'nessun file di configurazione messo da parte' "$(value leftover)" 0
ask diversion 'dpkg-divert --list /etc/xdg/autostart/orca-autostart.desktop | grep -c vabaxos-accessibility'
check "Orca parte ancora da VabaxOS (diversione)" "$(value diversion)" 1
ask autostart 'grep -c "^Exec=/usr/libexec/vabaxos/orca-start" /etc/xdg/autostart/orca-autostart.desktop'
check "avvio automatico di Orca di VabaxOS" "$(value autostart)" 1
ask rateafter "$ORCA_RATE"
check "impostazione di Orca conservata dall'aggiornamento" "$(value rateafter)" 63
ask welcomeafter "$(as_root 'test -f /var/lib/vabaxos/welcome-done && echo done')"
check 'benvenuto ancora segnato come fatto' "$(value welcomeafter)" "$(value welcomebefore)"
# Security updates by themselves, only two origins (ADR-0028).
ask unattended "dpkg-query -W -f '\${db:Status-Abbrev}' unattended-upgrades"
check 'unattended-upgrades installato con la versione nuova' "$(value unattended | tr -d ' ')" ii
ask origins 'apt-config dump Unattended-Upgrade::Origins-Pattern | grep -c "\"origin="'
check 'aggiornamenti automatici: solo due origini' "$(value origins)" 2
ask upgradetimer 'systemctl is-enabled apt-daily-upgrade.timer'
check 'controllo giornaliero della sicurezza attivo' "$(value upgradetimer)" enabled
ask allowed "$(as_root 'unattended-upgrade --dry-run -v 2>&1 | sed -n "s/.*Allowed origins are: //p" | head -n 1')" 900
check 'unattended-upgrades: sicurezza di Debian e pacchetti corretti di VabaxOS' "$(value allowed)" \
    "origin=Debian,codename=$VABAXOS_DISTRIBUTION-security,label=Debian-Security, origin=VabaxOS,codename=vabaxos,component=debian-fixes"
send "$(as_root 'tail -n 30 /var/log/unattended-upgrades/unattended-upgrades.log; dpkg --audit')"
sleep 3
power_off

# ---- 3. The updated system after a restart --------------------------------
LOG="$OUT/logs/test-upgrade-$STAMP-restart.log"
start_vm "$LOG" --silent-audio --memory 4096 --cpus 2 --disk "$DISK" --from-disk
printf 'INFO: avvio dopo l'\''aggiornamento (log: %s)\n' "$LOG"
# The login screen and the console speech before the serial login, as in
# test-install.sh: that login starts a second PipeWire.
wait_for 'login: *$' 'richiesta di accesso sulla console seriale' 600 || exit 1
sleep 45
press tab
check "schermata di accesso udibile (Orca) dopo l'aggiornamento" "$(record greeter 8)" yes
press ctrl-alt-f3
check "voce della console udibile dopo l'aggiornamento" "$(record console 10)" yes
login || exit 1
ask speech 'systemctl is-active espeakup'
ask gdm 'systemctl is-active gdm'
ask welcome 'systemctl show -p ConditionResult --value vabaxos-welcome'
ask failed "systemctl --failed --no-legend --plain | awk '{print \$1}' | tr '\n' ' '"
ask raterestart "$ORCA_RATE"
ask status 'vabaxctl status | grep -c "^Security updates: by themselves"'
check "voce della console (espeakup) dopo l'aggiornamento" "$(value speech)" active
check "schermata di accesso (GDM) dopo l'aggiornamento" "$(value gdm)" active
check "benvenuto non ripetuto dopo l'aggiornamento" "$(value welcome)" no
check "impostazione di Orca dopo il riavvio" "$(value raterestart)" 63
check 'vabaxctl dice che la sicurezza è automatica' "$(value status)" 1
printf 'INFO: servizi falliti: %s\n' "$(value failed)"
power_off

if [[ $FAILED -eq 0 ]]; then
    printf 'Risultato: test di aggiornamento superato.\n'
    exit 0
fi
printf 'Risultato: %d controlli falliti.\n' "$FAILED"
exit 1
