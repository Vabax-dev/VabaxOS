#!/usr/bin/env bash
# Installs live-build 1:20250814 from Debian testing "forky" on a Debian 13
# system (ADR-0017): the version in Debian 13 cannot build forky images well.
# The package comes from snapshot.debian.org and must match the SHA-256 below,
# which was checked against the signed Debian archive index.
#   sudo bash scripts/install-live-build.sh
set -euo pipefail

VERSION="1:20250814"
URL="http://snapshot.debian.org/archive/debian/20260920T000000Z/pool/main/l/live-build/live-build_20250814_all.deb"
SHA256="a4bffb8e6436ffba260f2e1c37be9dd04a4dacf52c38d7bbe454ec826ba52a4b"

if [[ $EUID -ne 0 ]]; then
    printf 'Serve root: sudo bash %s\n' "$0" >&2
    exit 1
fi

current="$(dpkg-query -W -f='${Version}' live-build 2>/dev/null || true)"
if [[ -n "$current" ]] && dpkg --compare-versions "$current" ge "$VERSION"; then
    printf 'OK: live-build %s già installato.\n' "$current"
    exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
deb="$tmp/live-build_20250814_all.deb"
if command -v curl >/dev/null; then
    curl -fsSL -o "$deb" "$URL"
else
    apt-get update -q && apt-get install -y -q --no-install-recommends curl ca-certificates
    curl -fsSL -o "$deb" "$URL"
fi
printf '%s  %s\n' "$SHA256" "$deb" | sha256sum -c --quiet || {
    printf 'ERRORE: il pacchetto scaricato non corrisponde all'\''impronta attesa.\n' >&2
    exit 1
}
chmod 0644 "$deb"
apt-get install -y -q --no-install-recommends "$deb"
printf 'OK: installato live-build %s.\n' "$(dpkg-query -W -f='${Version}' live-build)"
