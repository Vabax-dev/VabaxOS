#!/usr/bin/env bash
# Tests the VabaxOS APT archive (ADR-0020) without the real key:
#   bash tests/archive/test-archive.sh
# A throwaway key signs an archive built by scripts/build-archive.sh; APT,
# in a private directory, must read it with that key, see vabaxos-apt and
# its sources, and refuse it with another key. Needs reprepro, gnupg, apt.
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

# The archive, built with its own keyring.
GNUPGHOME="$WORK/unused" "$REPO/scripts/build-archive.sh" "$WORK/site"
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
    printf 'Types: deb\nURIs: file://%s/site/\nSuites: vabaxos\nComponents: main\nSigned-By: %s\n' \
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

out="$(apt_with "$WORK/other.asc")" || true
grep -q "NO_PUBKEY\|not signed\|is not signed" <<< "$out" || fail "apt ha accettato l'archivio con un'altra chiave: $out"

printf 'OK: archivio firmato letto da apt, rifiutato con un'\''altra chiave, sorgenti di vabaxos-apt corrette.\n'
