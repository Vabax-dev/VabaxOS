#!/usr/bin/env bash
# Upgrade test of the VabaxOS packages alone, in a few minutes (ADR-0020):
#   bash tests/packages/test-upgrade-packages.sh [OLD_REF]
#
# Installs the packages of OLD_REF (default: the last tag v*, or HEAD when
# there is none yet: the same packages with a lower version), then the
# packages of this checkout with a higher version, as dpkg does in an
# upgrade. It finds what breaks an upgrade before the ISO test
# (scripts/test-upgrade.sh):
# - a maintainer script that fails in an upgrade (preinst, postinst,
#   prerm, postrm with "upgrade");
# - a file moved to another package without Replaces (dpkg stops with
#   "trying to overwrite");
# - a diversion lost, a package left half installed (dpkg --audit);
# - a security update of Orca, whose autostart file VabaxOS diverts: it
#   must install by itself, with no question (ADR-0028), and leave
#   VabaxOS's Orca start in place.
#
# It installs packages into the system it runs on, ignoring dependencies:
# only in a throwaway container (the CI, debian:trixie), never on a
# computer in use.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ ! -f /.dockerenv && -z "${CI:-}" && -z "${VABAXOS_THROWAWAY_SYSTEM:-}" ]]; then
    printf 'ERRORE: installa pacchetti nel sistema: solo in un contenitore usa e getta (CI).\n' >&2
    exit 64
fi
[[ $EUID -eq 0 ]] || { printf 'ERRORE: serve root (dpkg -i).\n' >&2; exit 64; }
fail() { printf 'FALLITO: %s\n' "$*" >&2; exit 1; }

REF="${1:-$(git -C "$REPO" describe --tags --abbrev=0 --match 'v*' 2>/dev/null || echo HEAD)}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# The old packages, built by the old tree's own scripts.
mkdir -p "$WORK/old"
git -C "$REPO" archive "$REF" | tar -x -C "$WORK/old"
mkdir -p "$WORK/old/cache"
[[ -d "$REPO/cache/downloads" ]] && ln -s "$REPO/cache/downloads" "$WORK/old/cache/downloads"
(cd "$WORK/old" && git init -q && git add -A && \
    git -c user.name=t -c user.email=t@t commit -q --date="$(git -C "$REPO" log -1 --format=%cI "$REF")" -m old)
"$WORK/old/scripts/build-packages.sh" "$WORK/old-debs" >/dev/null 2>"$WORK/old.log" \
    || { tail -20 "$WORK/old.log"; fail "pacchetti di $REF"; }
# shellcheck source=/dev/null
. "$REPO/image/build.conf"
VABAXOS_VERSION="${VABAXOS_NEXT_VERSION}+upgradetest" "$REPO/scripts/build-packages.sh" "$WORK/new-debs" \
    >/dev/null 2>"$WORK/new.log" || { tail -20 "$WORK/new.log"; fail "pacchetti nuovi"; }
# The Kokoro model is large and has a fixed version.
rm -f "$WORK"/old-debs/vabaxos-kokoro-model_*.deb "$WORK"/new-debs/vabaxos-kokoro-model_*.deb

# A file moved from one package to another needs Replaces (and Breaks)
# on the old one, or dpkg refuses the upgrade.
files() {
    for deb in "$1"/*.deb; do
        package="$(dpkg-deb -f "$deb" Package)"
        dpkg-deb -c "$deb" | awk -v p="$package" '$1 !~ /^d/ {sub(/^\./, "", $6); print $6 "\t" p}'
    done | LC_ALL=C sort
}
files "$WORK/old-debs" > "$WORK/old-files"
files "$WORK/new-debs" > "$WORK/new-files"
LC_ALL=C join -t "$(printf '\t')" "$WORK/old-files" "$WORK/new-files" | while IFS="$(printf '\t')" read -r file owner package; do
    [[ "$owner" == "$package" ]] && continue
    deb="$(ls "$WORK"/new-debs/"${package}"_*.deb)"
    dpkg-deb -f "$deb" Replaces | tr ',' '\n' | sed 's/^ *//; s/[ (].*//' | grep -qx "$owner" \
        || printf '%s: da %s a %s senza Replaces\n' "$file" "$owner" "$package"
done > "$WORK/moved"
[[ -s "$WORK/moved" ]] && fail "file spostati fra pacchetti: $(cat "$WORK/moved")"

# The upgrade, as dpkg does it. Missing Debian dependencies are ignored
# (this is not the whole system): configuration errors are not.
export DEBIAN_FRONTEND=noninteractive
# Orca from Debian and the old packages in one dpkg run, as APT does in
# the ISO build: Orca only unpacked while the VabaxOS packages are unpacked
# left its autostart file as .dpkg-new once (ISO, 2026-09-27). Every dpkg
# reads from /dev/null: a question (a configuration file prompt) fails the
# test.
(cd "$WORK" && apt-get download -q orca >/dev/null) || fail "Orca non si scarica da Debian"
dpkg -i --force-depends "$WORK"/orca_*.deb "$WORK"/old-debs/*.deb > "$WORK/install-old.log" 2>&1 \
    < /dev/null || { tail -30 "$WORK/install-old.log"; fail "installazione di Orca e dei pacchetti di $REF"; }
left="$(find /etc -name '*.dpkg-dist' -o -name '*.dpkg-new' -o -name '*.dpkg-old')"
[[ -z "$left" ]] || fail "file di configurazione lasciati dall'installazione: $left"
diversions_before="$(dpkg-divert --list | grep -c vabaxos || true)"
dpkg -i --force-depends "$WORK"/new-debs/*.deb > "$WORK/upgrade.log" 2>&1 \
    < /dev/null || { tail -30 "$WORK/upgrade.log"; fail "aggiornamento ai pacchetti nuovi"; }
grep -q "trying to overwrite" "$WORK/upgrade.log" && fail "$(grep "trying to overwrite" "$WORK/upgrade.log")"
audit="$(dpkg --audit 2>&1 | grep -i vabaxos || true)"
[[ -z "$audit" ]] || fail "pacchetti VabaxOS installati a metà: $audit"
for deb in "$WORK"/new-debs/*.deb; do
    package="$(dpkg-deb -f "$deb" Package)"
    [[ "$(dpkg-query -W -f '${Version}' "$package")" == "$(dpkg-deb -f "$deb" Version)" ]] \
        || fail "$package non è alla versione nuova"
done
diversions_after="$(dpkg-divert --list | grep -c vabaxos || true)"
[[ "$diversions_after" -ge "$diversions_before" ]] \
    || fail "diversioni perse: $diversions_before prima, $diversions_after dopo"
[[ -z "$(find /etc -name '*.dpkg-dist' -o -name '*.dpkg-new')" ]] || fail "file di configurazione messi da parte"

# A security update of Orca that changes its autostart file.
autostart=/etc/xdg/autostart/orca-autostart.desktop
[[ "$(readlink "$autostart")" == /usr/share/vabaxos-accessibility/orca-autostart.desktop ]] \
    || fail "l'avvio di Orca non è quello di VabaxOS: $(ls -l "$autostart")"
dpkg-deb -R "$WORK"/orca_*.deb "$WORK/orca"
sed -i 's/^Version: .*/&+deb13u99/' "$WORK/orca/DEBIAN/control"
echo "# changed by a security update" >> "$WORK/orca/etc/xdg/autostart/orca-autostart.desktop"
dpkg-deb -b "$WORK/orca" "$WORK/orca-update.deb" >/dev/null
dpkg -i --force-depends "$WORK/orca-update.deb" > "$WORK/orca-update.log" 2>&1 < /dev/null \
    || { tail -20 "$WORK/orca-update.log"; fail "aggiornamento di sicurezza di Orca"; }
[[ "$(readlink "$autostart")" == /usr/share/vabaxos-accessibility/orca-autostart.desktop ]] \
    || fail "l'aggiornamento di Orca ha tolto l'avvio di VabaxOS"
grep -q "changed by a security update" "$autostart.orca" || fail "il file nuovo di Orca non è in $autostart.orca"

printf 'OK: aggiornamento da %s a %s: script dei pacchetti, file, diversioni (%s), aggiornamento di Orca.\n' \
    "$REF" "${VABAXOS_NEXT_VERSION}+upgradetest" "$diversions_after"
