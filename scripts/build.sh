#!/usr/bin/env bash
# Builds the VabaxOS ISO with live-build (ADR-0002).
#   ./scripts/build.sh                build the ISO into out/ (needs root through sudo)
#   ./scripts/build.sh --config-only  only run "lb config" on image/, without root (CI check)
# Environment:
#   VABAXOS_VERSION  release version such as 0.1.0-alpha.1 (ADR-0015).
#                    Without it the ISO gets a nightly name with date and commit.
# Output in out/: the ISO, SHA256SUMS, manifest.txt and logs/build-<date>.log.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="$REPO/image"
WORK="$REPO/build"
OUT="$REPO/out"
LB_ISO="live-image-amd64.hybrid.iso"
LB_PACKAGES="live-image-amd64.packages"

CONFIG_ONLY=false
case "${1:-}" in
    --config-only) CONFIG_ONLY=true ;;
    "") ;;
    *)
        printf 'Uso: %s [--config-only]\n' "$0" >&2
        exit 64
        ;;
esac

say() {
    # Spoken summary for the workstation (ADR-0013); silent in CI and without espeak-ng.
    if [[ -z "${CI:-}" ]] && command -v espeak-ng >/dev/null; then
        espeak-ng -v it "$1" 2>/dev/null || true
    fi
}

die() {
    printf 'ERRORE: %s\n' "$*" >&2
    exit 1
}

# live-build needs root for the chroot. On the workstation sudo is allowed
# without a password for /usr/bin/lb only (CLAUDE.md); in CI we are root.
lb_root() {
    if [[ $EUID -eq 0 ]]; then
        lb "$@"
    else
        sudo /usr/bin/lb "$@"
    fi
}

# Copies image/ into a build directory and runs "lb config" there.
# With a second argument "packages", the VabaxOS packages (packages/) are
# built into config/packages.chroot, where live-build installs them.
prepare_config() {
    local dir="$1"
    rm -rf "$dir/auto" "$dir/config" "$dir/build.conf"
    mkdir -p "$dir"
    cp -a "$IMAGE/auto" "$IMAGE/config" "$IMAGE/build.conf" "$dir/"
    if [[ "${2:-}" == packages ]]; then
        "$REPO/scripts/build-packages.sh" "$dir/config/packages.chroot"
    fi
    (cd "$dir" && lb config)
}

command -v lb >/dev/null || die "live-build non è installato. Esegui scripts/check-deps.sh."

if [[ "$CONFIG_ONLY" == true ]]; then
    TMP="$(mktemp -d)"
    trap 'rm -rf "$TMP"' EXIT
    prepare_config "$TMP"
    printf 'OK: la configurazione di live-build è valida.\n'
    exit 0
fi

STARTED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
mkdir -p "$OUT/logs"
LOG="$OUT/logs/build-$(date +%Y-%m-%d-%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1

on_exit() {
    local status=$?
    if [[ $status -ne 0 ]]; then
        printf '\nCostruzione fallita (codice %d). Log: %s\n' "$status" "$LOG"
        say "Costruzione della ISO fallita."
    fi
}
trap on_exit EXIT

printf 'Costruzione di VabaxOS, inizio %s\n' "$STARTED"
printf 'Log: %s\n\n' "$LOG"

"$REPO/scripts/check-deps.sh" || die "l'ambiente non è pronto (vedi sopra)."
printf '\n'

# shellcheck source=/dev/null
. "$IMAGE/build.conf"

COMMIT="$(git -C "$REPO" rev-parse HEAD)"
DIRTY=no
[[ -z "$(git -C "$REPO" status --porcelain)" ]] || DIRTY=yes
if [[ -n "${VABAXOS_VERSION:-}" ]]; then
    ISO_NAME="VabaxOS-$VABAXOS_VERSION-amd64.iso"
else
    ISO_NAME="VabaxOS-nightly-$(date -u +%Y%m%d)-${COMMIT:0:7}-amd64.iso"
fi

# Clean the previous build and configure again. live-build caches the
# bootstrapped base system: keep the cache only while the snapshot and the
# lb config options that shape the base system are the same as in the build
# that filled it. Boot parameters and package lists do not count here.
CACHE_KEY="$({ cat "$IMAGE/build.conf"
    grep -E -- '--(mode|distribution|architecture|archive-areas|mirror-bootstrap|mirror-chroot|debootstrap-options|keyring-packages)' "$IMAGE/auto/config"
} | sha256sum | cut -d' ' -f1)"
CACHE_STAMP="$WORK/.vabaxos-cache-key"
if [[ -d "$WORK" ]]; then
    if [[ -f "$CACHE_STAMP" && "$(cat "$CACHE_STAMP")" == "$CACHE_KEY" ]]; then
        (cd "$WORK" && lb_root clean)
    else
        printf 'Snapshot o opzioni di live-build cambiati: cancello anche la cache.\n'
        (cd "$WORK" && lb_root clean --purge)
    fi
fi
prepare_config "$WORK" packages
printf '%s\n' "$CACHE_KEY" > "$CACHE_STAMP"

printf '\nlive-build: inizio (snapshot Debian %s)\n' "$VABAXOS_SNAPSHOT"
(cd "$WORK" && lb_root build)
[[ -f "$WORK/$LB_ISO" ]] || die "live-build non ha prodotto $LB_ISO."

# Results: one ISO at a time in out/; logs are never overwritten.
rm -f "$OUT"/*.iso "$OUT/SHA256SUMS" "$OUT/manifest.txt"
cp "$WORK/$LB_ISO" "$OUT/$ISO_NAME"
(cd "$OUT" && sha256sum "$ISO_NAME" > SHA256SUMS)

# shellcheck source=/dev/null
. "$WORK/config/all"
{
    printf '# VabaxOS build manifest (ADR-0002)\n'
    printf 'iso: %s\n' "$ISO_NAME"
    printf 'iso-sha256: %s\n' "$(cut -d' ' -f1 "$OUT/SHA256SUMS")"
    printf 'squashfs-sha256: %s\n' "$(sha256sum "$WORK/binary/live/filesystem.squashfs" | cut -d' ' -f1)"
    printf 'version: %s\n' "${VABAXOS_VERSION:-nightly}"
    printf 'git-commit: %s\n' "$COMMIT"
    printf 'git-uncommitted-changes: %s\n' "$DIRTY"
    printf 'debian-distribution: %s\n' "$VABAXOS_DISTRIBUTION"
    printf 'debian-snapshot: %s\n' "$VABAXOS_SNAPSHOT"
    printf 'source-date-epoch: %s\n' "$SOURCE_DATE_EPOCH"
    printf 'live-build: %s\n' "$(dpkg-query -W -f='${Version}' live-build)"
    printf 'kernel: %s\n' "$(awk '/^linux-image-[0-9]/ {print $1 " " $2}' "$WORK/$LB_PACKAGES" | paste -sd ' ')"
    printf 'built-at: %s\n' "$STARTED"
    # shellcheck source=/dev/null
    printf 'build-host: %s\n' "$(. /etc/os-release && printf '%s' "$PRETTY_NAME")"
    printf '\n# Packages in the live system (name version)\n'
    cat "$WORK/$LB_PACKAGES"
} > "$OUT/manifest.txt"

printf '\nCostruzione completata.\n'
printf 'ISO: %s (%s MB)\n' "$OUT/$ISO_NAME" "$(( $(stat -c %s "$OUT/$ISO_NAME") / 1048576 ))"
printf 'Checksum: %s\n' "$OUT/SHA256SUMS"
printf 'Manifest: %s\n' "$OUT/manifest.txt"
say "Costruzione della ISO completata."
