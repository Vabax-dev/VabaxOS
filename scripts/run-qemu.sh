#!/usr/bin/env bash
# Starts a VabaxOS ISO in a QEMU virtual machine with sound (ADR-0013).
#   ./scripts/run-qemu.sh [options] [ISO] [-- extra QEMU options]
# Without ISO it starts the ISO in out/.
#
# Options:
#   --secure-boot      UEFI with Secure Boot on and the Microsoft keys (ADR-0003)
#   --bios             legacy BIOS instead of UEFI
#   --headless         no window (the VM cannot be used from the keyboard)
#   --no-audio         no sound card and no PC speaker
#   --silent-audio     sound card and PC speaker present, but nothing is heard
#                      (automatic tests: speech services still find a card)
#   --memory MB        memory of the VM (default 4096)
#   --serial-log FILE  write the first serial port to FILE
#                      (default out/logs/qemu-serial-<date>.log)
#   --serial-tcp PORT  first serial port on 127.0.0.1:PORT instead of a file;
#                      QEMU waits for a connection before starting (scripts/test-boot.sh)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$REPO/out"
OVMF=/usr/share/OVMF

usage() {
    sed -n '2,/^set -euo/p' "${BASH_SOURCE[0]}" | sed -e '$d' -e 's/^# \{0,1\}//'
    exit "${1:-0}"
}

die() {
    printf 'ERRORE: %s\n' "$*" >&2
    exit 1
}

FIRMWARE=uefi
HEADLESS=false
AUDIO=true
MEMORY=4096
SERIAL_LOG=""
SERIAL_TCP=""
ISO=""
EXTRA=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --secure-boot) FIRMWARE=secure-boot ;;
        --bios) FIRMWARE=bios ;;
        --headless) HEADLESS=true ;;
        --no-audio) AUDIO=false ;;
        --silent-audio) AUDIO=silent ;;
        --memory) MEMORY="${2:?--memory vuole un numero}"; shift ;;
        --serial-log) SERIAL_LOG="${2:?--serial-log vuole un file}"; shift ;;
        --serial-tcp) SERIAL_TCP="${2:?--serial-tcp vuole una porta}"; shift ;;
        -h | --help) usage 0 ;;
        --) shift; EXTRA=("$@"); break ;;
        -*) printf 'Opzione sconosciuta: %s\n\n' "$1" >&2; usage 64 >&2 ;;
        *) ISO="$1" ;;
    esac
    shift
done

if [[ -z "$ISO" ]]; then
    shopt -s nullglob
    ISOS=("$OUT"/*.iso)
    shopt -u nullglob
    [[ ${#ISOS[@]} -gt 0 ]] || die "nessuna ISO in $OUT. Prima esegui scripts/build.sh."
    [[ ${#ISOS[@]} -eq 1 ]] || die "in $OUT ci sono più ISO: indica quale avviare."
    ISO="${ISOS[0]}"
fi
[[ -f "$ISO" ]] || die "ISO non trovata: $ISO"

ARGS=(-name VabaxOS -m "$MEMORY" -smp 2 -boot d -no-user-config)
ARGS+=(-drive "file=$ISO,media=cdrom,readonly=on")
ARGS+=(-nic "user,model=virtio-net-pci")

if [[ -r /dev/kvm && -w /dev/kvm ]]; then
    ARGS+=(-accel kvm -cpu host)
else
    printf 'AVVISO: KVM non disponibile, la macchina virtuale sarà lenta.\n' >&2
    ARGS+=(-accel tcg)
fi

MACHINE=q35
case "$FIRMWARE" in
    uefi | secure-boot)
        if [[ "$FIRMWARE" == secure-boot ]]; then
            CODE="$OVMF/OVMF_CODE_4M.ms.fd"
            VARS_TEMPLATE="$OVMF/OVMF_VARS_4M.ms.fd"
            # The Secure Boot firmware needs SMM to protect its variables.
            MACHINE+=",smm=on"
            ARGS+=(-global "driver=cfi.pflash01,property=secure,value=on")
        else
            CODE="$OVMF/OVMF_CODE_4M.fd"
            VARS_TEMPLATE="$OVMF/OVMF_VARS_4M.fd"
        fi
        [[ -f "$CODE" && -f "$VARS_TEMPLATE" ]] || die "firmware OVMF mancante: installa il pacchetto ovmf."
        # Every run starts from clean UEFI variables.
        VARS="$(mktemp --suffix=.fd)"
        trap 'rm -f "$VARS"' EXIT
        cp "$VARS_TEMPLATE" "$VARS"
        ARGS+=(-drive "if=pflash,format=raw,unit=0,readonly=on,file=$CODE")
        ARGS+=(-drive "if=pflash,format=raw,unit=1,file=$VARS")
        ;;
    bios) ;;
esac

if [[ "$AUDIO" != false ]]; then
    if [[ "$AUDIO" == silent ]]; then
        ARGS+=(-audiodev "none,id=snd0")
    else
        # PulseAudio: on WSL2 this is WSLg, so the VM speaks through the PC.
        ARGS+=(-audiodev "pa,id=snd0")
    fi
    ARGS+=(-device intel-hda -device "hda-duplex,audiodev=snd0")
    # PC speaker, for the beep of the boot menu (ADR-0003, ADR-0014).
    MACHINE+=",pcspk-audiodev=snd0"
fi
ARGS+=(-machine "$MACHINE")

if [[ "$HEADLESS" == true ]]; then
    ARGS+=(-display none)
fi

if [[ -n "$SERIAL_TCP" ]]; then
    ARGS+=(-chardev "socket,id=serial0,host=127.0.0.1,port=$SERIAL_TCP,server=on,wait=on")
    ARGS+=(-serial chardev:serial0)
else
    if [[ -z "$SERIAL_LOG" ]]; then
        mkdir -p "$OUT/logs"
        SERIAL_LOG="$OUT/logs/qemu-serial-$(date +%Y-%m-%d-%H%M%S).log"
    fi
    ARGS+=(-serial "file:$SERIAL_LOG")
    printf 'Console seriale: %s\n' "$SERIAL_LOG"
fi

printf 'Avvio %s (%s)\n' "$(basename "$ISO")" "$FIRMWARE"
qemu-system-x86_64 "${ARGS[@]}" "${EXTRA[@]}"
