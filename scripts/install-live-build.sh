#!/usr/bin/env bash
# Installs live-build from its Git repository at a fixed commit (ADR-0017).
#   sudo bash scripts/install-live-build.sh
#
# Why not the Debian package: live-build 1:20250814, the newest in Debian
# (also in forky), cannot build a forky image with the installer. It still
# requires libfuse2, which forky no longer has. The Git version fixes this
# ("Installer: stop requiring fuse2", 2026-01-02) and brings installer fixes
# we need: offline installation with speech and Braille in the installed
# system, locale from d-i, kernel filter for the installer.
#
# The commit is fixed: a Git commit hash also checks the contents, so the
# same files are installed on every machine. The package is built here,
# without debhelper, with the same files as Debian's (manual pages in
# English only) and the version 1:20250814+git<date>.<commit>, which is
# newer than Debian's.
set -euo pipefail

COMMIT="531cdb9854e04d08c3c3770463454d8a5e91b129"
DATE="20260913"
REPO_URL="https://salsa.debian.org/live-team/live-build.git"
VERSION="1:20250814+git${DATE}.${COMMIT:0:8}"

if [[ $EUID -ne 0 ]]; then
    printf 'Serve root: sudo bash %s\n' "$0" >&2
    exit 1
fi

current="$(dpkg-query -W -f='${Version}' live-build 2>/dev/null || true)"
if [[ "$current" == "$VERSION" ]]; then
    printf 'OK: live-build %s già installato.\n' "$current"
    exit 0
fi

need=()
for pkg in git ca-certificates debootstrap cpio; do
    dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q 'ok installed' || need+=("$pkg")
done
if ((${#need[@]})); then
    apt-get update -q
    apt-get install -y -q --no-install-recommends "${need[@]}"
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
src="$tmp/live-build"
git init -q "$src"
git -C "$src" fetch -q --depth 1 "$REPO_URL" "$COMMIT"
git -C "$src" checkout -q FETCH_HEAD
if [[ "$(git -C "$src" rev-parse HEAD)" != "$COMMIT" ]]; then
    printf 'ERRORE: il commit scaricato non è %s.\n' "$COMMIT" >&2
    exit 1
fi

# The files of Debian's package (Makefile "install", without translated
# manual pages, which need po4a).
root="$tmp/root"
mkdir -p "$root/usr/share/live/build" "$root/usr/bin" "$root/usr/lib/live" \
    "$root/usr/share/doc/live-build" "$root/DEBIAN"
(
    cd "$src"
    cp -r data functions "$root/usr/share/live/build"
    printf '%s\n' "${VERSION#1:}" > "$root/usr/share/live/build/VERSION"
    cp -r share/* "$root/usr/share/live/build"
    cp -a frontend/* "$root/usr/bin"
    cp -a scripts/* "$root/usr/lib/live"
    cp -r examples "$root/usr/share/doc/live-build"
    cp debian/copyright "$root/usr/share/doc/live-build/copyright"
    for page in manpages/en/*; do
        section="$(basename "$page" | awk -F. '{ print $2 }')"
        install -D -m 0644 "$page" "$root/usr/share/man/man$section/$(basename "$page")"
    done
)
cat > "$root/DEBIAN/control" <<EOF
Package: live-build
Version: $VERSION
Architecture: all
Maintainer: VabaxOS <https://github.com/Vabax-dev/VabaxOS>
Depends: cpio, debootstrap
Recommends: apt-utils, bzip2, cryptsetup, file, rsync, systemd-container, wget, xz-utils
Suggests: e2fsprogs, eatmydata, git, mtd-utils, parted
Section: misc
Priority: optional
Homepage: https://wiki.debian.org/DebianLive
Description: Live System Build Components (Git ${COMMIT:0:8}, built by VabaxOS)
 live-build from its Git repository at commit $COMMIT,
 packaged by scripts/install-live-build.sh of VabaxOS.
EOF
deb="$tmp/live-build.deb"
dpkg-deb --root-owner-group -Zxz --build "$root" "$deb" >/dev/null
chmod 0644 "$deb"
apt-get install -y -q --no-install-recommends --allow-downgrades "$deb"
printf 'OK: installato live-build %s.\n' "$(dpkg-query -W -f='${Version}' live-build)"
