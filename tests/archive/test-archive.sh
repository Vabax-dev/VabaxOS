#!/usr/bin/env bash
# Tests the VabaxOS APT archive (ADR-0020) without the real key:
#   bash tests/archive/test-archive.sh
# A throwaway key signs an archive built by scripts/build-archive.sh; APT,
# in a private directory, must read it with that key, see vabaxos-apt and
# its sources, and refuse it with another key. A made-up Debian package
# rebuilt with VabaxOS's fixes goes to the component debian-fixes, which
# unattended-upgrades installs by itself (ADR-0028). Needs reprepro, gnupg,
# apt.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK="$(mktemp -d)"
KEY="$REPO/keys/vabaxos-archive.asc"
cleanup() {
    rm -rf "$WORK"
    # The throwaway public key must never stay in keys/.
    if [[ -f "$WORK.keep" ]]; then mv "$WORK.keep" "$KEY"; else rm -f "$KEY"; fi
}
[[ -f "$KEY" ]] && cp -p "$KEY" "$WORK.keep"
trap cleanup EXIT
fail() { printf 'FALLITO: %s\n' "$*" >&2; exit 1; }

export GNUPGHOME="$WORK/g"
mkdir -m 0700 "$GNUPGHOME"
gpg --batch --quiet --passphrase '' --quick-generate-key "VabaxOS test archive key" ed25519 sign 1d
gpg --batch --quiet --passphrase '' --quick-generate-key "Some other key" ed25519 sign 1d
gpg --batch --armor --export "VabaxOS test archive key" > "$KEY"
gpg --batch --armor --export "Some other key" > "$WORK/other.asc"
VABAXOS_ARCHIVE_KEY="$(gpg --batch --armor --export-secret-keys "VabaxOS test archive key")"
export VABAXOS_ARCHIVE_KEY

# A Debian package rebuilt by scripts/build-debian-patched.sh (made up).
mkdir -p "$WORK/fix/DEBIAN" "$WORK/fixes"
printf 'Package: vabaxos-test-fixed\nVersion: 1.0-1+deb13u1+0vabaxos1\nArchitecture: all\nSection: misc\nPriority: optional\nMaintainer: t <t@t>\nDescription: t\n' \
    > "$WORK/fix/DEBIAN/control"
dpkg-deb --build "$WORK/fix" "$WORK/fixes/vabaxos-test-fixed_1.0-1+deb13u1+0vabaxos1_all.deb" >/dev/null

# The archive, built with its own keyring.
GNUPGHOME="$WORK/unused" VABAXOS_DEBIAN_FIXES="$WORK/fixes" "$REPO/scripts/build-archive.sh" "$WORK/site"
for f in dists/vabaxos/InRelease dists/vabaxos/Release.gpg vabaxos-archive.asc; do
    [[ -f "$WORK/site/$f" ]] || fail "manca $f"
done
cmp -s "$KEY" "$WORK/site/vabaxos-archive.asc" || fail "la chiave pubblicata non è keys/vabaxos-archive.asc"

# APT in a private directory, with the archive as its only source.
ROOT="$WORK/apt"
APT_OPTS=(-o "Dir::State=$ROOT" -o "Dir::State::Lists=$ROOT/lists" -o "Dir::State::status=$ROOT/status"
    -o "Dir::Cache=$ROOT/cache" -o "Dir::Etc::SourceList=/dev/null" -o "Dir::Etc::SourceParts=$ROOT/parts"
    -o "Dir::Etc::Preferences=/dev/null" -o "Dir::Etc::PreferencesParts=$ROOT/prefs"
    -o "APT::Architecture=amd64" -o "Debug::NoLocking=1" -o "APT::Sandbox::User=root")
apt_with() {
    rm -rf "$ROOT"
    mkdir -p "$ROOT/lists/partial" "$ROOT/cache/archives/partial" "$ROOT/parts" "$ROOT/prefs"
    : > "$ROOT/status"
    printf 'Types: deb\nURIs: file://%s/site/\nSuites: vabaxos\nComponents: main debian-fixes\nSigned-By: %s\n' \
        "$WORK" "$1" > "$ROOT/parts/vabaxos.sources"
    apt-get "${APT_OPTS[@]}" update 2>&1
}

out="$(apt_with "$KEY")" || fail "apt update con la chiave giusta: $out"
grep -q "^E:\|^W:" <<< "$out" && fail "avvisi di apt con la chiave giusta: $out"
policy="$(apt-cache "${APT_OPTS[@]}" policy vabaxos-apt vabaxos-voice vabaxos-kokoro-model)"
grep -A2 '^vabaxos-apt:' <<< "$policy" | grep -q 'Candidate: 0\.1' || fail "vabaxos-apt non è nell'archivio: $policy"
grep -A2 '^vabaxos-voice:' <<< "$policy" | grep -q 'Candidate: 0\.1' || fail "vabaxos-voice non è nell'archivio: $policy"
# Over the 100 MB of GitHub Pages: only in the ISO.
grep -A2 '^vabaxos-kokoro-model:' <<< "$policy" | grep -q 'Candidate: (none)' || fail "il modello Kokoro non doveva essere nell'archivio: $policy"

# The rebuilt Debian packages: in debian-fixes, with the values that the
# pattern of apt.conf.d/52vabaxos-security matches, not in main.
policy="$(apt-cache "${APT_OPTS[@]}" policy vabaxos-test-fixed)"
grep -q 'Candidate: 1.0-1+deb13u1+0vabaxos1' <<< "$policy" || fail "il pacchetto corretto non è nell'archivio: $policy"
grep -q ' vabaxos/debian-fixes ' <<< "$policy" || fail "il pacchetto corretto non è nella componente debian-fixes: $policy"
grep -q ' vabaxos/main ' <<< "$(apt-cache "${APT_OPTS[@]}" policy vabaxos-voice)" || fail "vabaxos-voice non è in main"
releases="$(apt-cache "${APT_OPTS[@]}" policy)"
grep -q 'release o=VabaxOS,a=vabaxos,n=vabaxos,l=VabaxOS,c=debian-fixes' <<< "$releases" \
    || fail "debian-fixes senza origin=VabaxOS e codename=vabaxos: $releases"
# A security update of Debian wins over the rebuild of the older version,
# and the rebuild of the new one wins over it (ADR-0028).
dpkg --compare-versions 1.0-1+0vabaxos1 gt 1.0-1 || fail "+0vabaxos1 non supera la versione di Debian"
dpkg --compare-versions 1.0-1+deb13u1 gt 1.0-1+0vabaxos1 || fail "+deb13u1 non supera +0vabaxos1"
dpkg --compare-versions 1.0-1+b1 gt 1.0-1+0vabaxos1 || fail "+b1 non supera +0vabaxos1"
dpkg --compare-versions 1.0-1+deb13u1+0vabaxos1 gt 1.0-1+deb13u1 || fail "la ricostruzione non supera +deb13u1"

# The sources that vabaxos-apt installs.
deb="$(find "$WORK/site/pool" -name 'vabaxos-apt_*.deb')"
dpkg-deb -x "$deb" "$WORK/pkg"
grep -q '^Signed-By: /usr/share/keyrings/vabaxos-archive-keyring.asc$' "$WORK/pkg/etc/apt/sources.list.d/vabaxos.sources" \
    || fail "vabaxos.sources senza la chiave dell'archivio"
cmp -s "$KEY" "$WORK/pkg/usr/share/keyrings/vabaxos-archive-keyring.asc" || fail "vabaxos-apt non ha la chiave dell'archivio"
# shellcheck source=/dev/null
. "$REPO/image/build.conf"
grep -q "^URIs: https://snapshot.debian.org/archive/debian/$VABAXOS_SNAPSHOT/$" "$WORK/pkg/etc/apt/sources.list.d/vabaxos-debian.sources" \
    || fail "vabaxos-debian.sources non usa la data di image/build.conf"
# Security of today, not at the date (ADR-0028), installed by itself.
grep -q '^URIs: https://security.debian.org/debian-security/$' "$WORK/pkg/etc/apt/sources.list.d/vabaxos-debian.sources" \
    || fail "vabaxos-debian.sources senza la sicurezza di Debian di oggi"
grep -q "debian-security/$VABAXOS_SNAPSHOT" "$WORK/pkg/etc/apt/sources.list.d/vabaxos-debian.sources" \
    && fail "la sicurezza non deve essere a una data"
grep -q '^Components: main debian-fixes$' "$WORK/pkg/etc/apt/sources.list.d/vabaxos.sources" \
    || fail "vabaxos.sources senza la componente debian-fixes"
conf="$WORK/pkg/etc/apt/apt.conf.d/52vabaxos-security"
# shellcheck disable=SC2016 # the literal ${distro_codename} of unattended-upgrades
grep -q '"origin=Debian,codename=${distro_codename}-security,label=Debian-Security";' "$conf" || fail "52vabaxos-security senza la sicurezza di Debian"
grep -q '"origin=VabaxOS,codename=vabaxos,component=debian-fixes";' "$conf" || fail "52vabaxos-security senza debian-fixes"
grep -q '^#clear Unattended-Upgrade::Origins-Pattern;' "$conf" || fail "52vabaxos-security non toglie l'elenco di Debian"
[[ "$(grep -c '"origin=' "$conf")" == 2 ]] || fail "52vabaxos-security: solo due origini"
# What APT reads: the two origins only, after Debian's own list.
if [[ -f /etc/apt/apt.conf.d/50unattended-upgrades ]]; then
    mkdir -p "$WORK/conf.d"
    cp /etc/apt/apt.conf.d/50unattended-upgrades "$conf" "$WORK/conf.d/"
    printf 'Dir::Etc::Parts "%s/conf.d";\n' "$WORK" > "$WORK/apt.conf"
    patterns="$(APT_CONFIG="$WORK/apt.conf" apt-config dump Unattended-Upgrade::Origins-Pattern | grep -c '"origin=' || true)"
    [[ "$patterns" == 2 ]] || fail "APT legge $patterns origini per unattended-upgrades invece di 2"
fi
grep -q 'unattended-upgrades' <<< "$(dpkg-deb -f "$deb" Depends)" || fail "vabaxos-apt non dipende da unattended-upgrades"

out="$(apt_with "$WORK/other.asc")" || true
grep -q "NO_PUBKEY\|not signed\|is not signed" <<< "$out" || fail "apt ha accettato l'archivio con un'altra chiave: $out"

printf 'OK: archivio firmato letto da apt, rifiutato con un'\''altra chiave, sorgenti di vabaxos-apt corrette, pacchetti corretti in debian-fixes, sicurezza automatica.\n'
