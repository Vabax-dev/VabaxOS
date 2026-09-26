#!/usr/bin/env bash
# Tests the VabaxOS APT archive (ADR-0026) with a throwaway key: the
# keyring package carries the key and the sources, APT trusts the signed
# archive through Signed-By and offers the VabaxOS packages, and refuses
# an archive changed after signing. No root needed, nothing installed.
#   bash tests/apt/test_apt_repo.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK="$(mktemp -d)"
trap 'gpgconf --homedir "$WORK/gnupg" --kill all 2>/dev/null || true; rm -rf "$WORK"' EXIT
FAILED=0
check() {
    if [[ "$2" == "$3" ]]; then
        printf 'OK: %s\n' "$1"
    else
        printf 'FALLITO: %s: %s (atteso: %s)\n' "$1" "$2" "$3"
        FAILED=$((FAILED + 1))
    fi
}

# 1. A throwaway key, as create-project-key.sh makes the real one:
#    Ed25519, a key that only certifies and a subkey that signs.
export GNUPGHOME="$WORK/gnupg"
mkdir -m 700 "$GNUPGHOME"
gpg --batch --quiet --passphrase '' --quick-generate-key "VabaxOS Test Key <test@invalid>" ed25519 cert never
FPR="$(gpg --batch --with-colons --list-keys | awk -F: '$1 == "fpr" {print $10; exit}')"
gpg --batch --quiet --passphrase '' --quick-add-key "$FPR" ed25519 sign 1d
gpg --batch --armor --export "$FPR" > "$WORK/test-key.asc"

# 2. The packages, with the throwaway key in vabaxos-archive-keyring.
VABAXOS_ARCHIVE_KEY="$WORK/test-key.asc" "$REPO/scripts/build-packages.sh" "$WORK/packages" >/dev/null 2>&1
dpkg-deb -x "$WORK"/packages/vabaxos-archive-keyring_*.deb "$WORK/keyring"
check 'la chiave è nel pacchetto' "$(test -s "$WORK/keyring/usr/share/keyrings/vabaxos-archive-keyring.pgp" && echo yes)" yes
check 'le sorgenti sono in formato deb822, disattivate' \
    "$(grep -c '^Signed-By: /usr/share/keyrings/vabaxos-archive-keyring.pgp$\|^Enabled: no$' "$WORK/keyring/etc/apt/sources.list.d/vabaxos.sources")" 2

# 3. The archive, signed.
"$REPO/scripts/apt-repo.sh" --packages "$WORK/packages" --out "$WORK/apt" --key "$FPR" >/dev/null
check 'InRelease firmato' "$(gpgv --keyring "$WORK/keyring/usr/share/keyrings/vabaxos-archive-keyring.pgp" "$WORK/apt/dists/forky/InRelease" 2>/dev/null && echo yes)" yes

# 4. APT reads it as a system would: the sources of the package, enabled
#    and pointing to the folder, and the key from the package.
apt_test() {
    local tool=apt-get root="$1"; shift
    if [[ "$1" == policy ]]; then tool=apt-cache; fi
    "$tool" -q -o Debug::NoLocking=1 -o APT::Sandbox::User=root \
        -o Dir::State="$root/state" -o Dir::Cache="$root/cache" \
        -o Dir::Etc::SourceList=/dev/null -o Dir::Etc::SourceParts="$root/sources" \
        -o Dir::Etc::Trusted=/dev/null -o Dir::Etc::TrustedParts=/dev/null \
        -o Dir::Etc::Preferences=/dev/null -o Dir::Etc::PreferencesParts=/dev/null \
        -o APT::Architecture=amd64 "$@"
}
apt_root() {
    local root="$1" archive="$2"
    mkdir -p "$root/state/lists/partial" "$root/cache/archives/partial" "$root/sources"
    touch "$root/state/status"
    sed -e "s|^URIs: .*|URIs: file://$archive|" -e 's/^Enabled: no$/Enabled: yes/' \
        -e "s|^Signed-By: .*|Signed-By: $WORK/keyring/usr/share/keyrings/vabaxos-archive-keyring.pgp|" \
        "$WORK/keyring/etc/apt/sources.list.d/vabaxos.sources" > "$root/sources/vabaxos.sources"
}
apt_root "$WORK/root" "$WORK/apt"
if apt_test "$WORK/root" update > "$WORK/update.log" 2>&1; then
    update=yes
else
    update=no
    sed 's/^/  /' "$WORK/update.log"
fi
check 'apt update con la chiave del pacchetto' "$update" yes
version="$(dpkg-deb -f "$WORK"/packages/vabaxos-accessibility_*.deb Version)"
apt_test "$WORK/root" policy vabaxos-accessibility > "$WORK/policy.log" 2>&1 || true
offered="$(grep -c "Candidate: $version\$" "$WORK/policy.log")" || true
[[ "$offered" == 1 ]] || sed 's/^/  /' "$WORK/policy.log"
check 'APT offre i pacchetti VabaxOS' "$offered" 1
check 'origine dell'"'"'archivio: VabaxOS' "$(grep -c '^Origin: VabaxOS$' "$WORK/apt/dists/forky/Release")" 1

# 5. An archive changed after signing is refused.
cp -a "$WORK/apt" "$WORK/apt-changed"
sed -i 's/^Origin: VabaxOS$/Origin: Somebody else/' "$WORK/apt-changed/dists/forky/InRelease"
rm -f "$WORK/apt-changed/dists/forky/Release.gpg"
apt_root "$WORK/root2" "$WORK/apt-changed"
if apt_test "$WORK/root2" update > "$WORK/update2.log" 2>&1 && ! grep -q '^W:\|^E:' "$WORK/update2.log"; then
    refused=no
else
    refused=yes
fi
check 'un archivio cambiato dopo la firma è rifiutato' "$refused" yes

# 6. Versions grow: a later commit gives a later version.
older="$(date -u -d @1790000000 +%Y%m%d.%H%M%S)"
check 'la versione di sviluppo viene dopo la versione di VERSION' \
    "$(dpkg --compare-versions "$(tr -d '[:space:]' < "$REPO/packages/VERSION")" lt "$version" && echo yes)" yes
check 'una costruzione più recente ha una versione più alta' \
    "$(dpkg --compare-versions "$(tr -d '[:space:]' < "$REPO/packages/VERSION")+git$older" lt "$version" && echo yes)" yes

if [[ "$FAILED" -eq 0 ]]; then
    printf 'Risultato: archivio APT provato.\n'
else
    printf 'Risultato: %d controlli falliti.\n' "$FAILED"
fi
exit "$FAILED"
