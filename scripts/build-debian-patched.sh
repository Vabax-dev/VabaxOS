#!/bin/sh
# Rebuilds Debian packages with VabaxOS's small fixes (ADR-0026).
#   build-debian-patched.sh [--installed] [--install] [--out DIR]
#                           [--print-versions] [PATCHES_DIR]
#
# PATCHES_DIR (default: patches/debian of the repository, or the folder of
# this script inside the ISO) holds one folder per Debian source package,
# with
#   series     the fixes, in the order they are added (quilt)
#   *.patch    the fixes
#   packages   the binary packages that replace Debian's
# For each source it downloads Debian's source, adds the fixes and builds
# it with the version <Debian's>+0vabaxos1. "+0vabaxos1" sorts after
# Debian's version and before any update of it ("+deb13u1" of
# trixie-security, "+b1"): a security update of Debian always wins over an
# older fixed package (ADR-0028), until this rebuilds the new version.
#
#   --installed  the version of the installed packages (inside the ISO's
#                chroot, hook 0400-vabaxos-debian-patched); otherwise the
#                newest version APT knows (the VabaxOS archive, every day,
#                with trixie-security)
#   --install    install the rebuilt packages that are installed now
#   --out DIR    copy every rebuilt package of the sources to DIR (all of
#                them, so every binary package of a source has the same
#                version and none holds the others back)
#   --print-versions  only print "source version" for each source, the
#                versions that would be rebuilt (the CI's cache key)
#
# Needs root on a Debian system with APT (the build dependencies are
# installed, and removed at the end); deb-src entries are added for the
# sources of APT's deb entries.
set -e

INSTALLED=false
INSTALL=false
PRINT=false
OUT=""
while [ $# -gt 0 ]; do
    case "$1" in
        --installed) INSTALLED=true ;;
        --install) INSTALL=true ;;
        --out) OUT="$2"; shift ;;
        --print-versions) PRINT=true ;;
        -*) echo "build-debian-patched: unknown option $1" >&2; exit 2 ;;
        *) break ;;
    esac
    shift
done
here="$(cd "$(dirname "$0")" && pwd)"
if [ -n "$1" ]; then
    top="$1"
elif [ -d "$here/../patches/debian" ]; then
    top="$here/../patches/debian"
else
    top="$here"
fi
top="$(cd "$top" && pwd)"

export DEBIAN_FRONTEND=noninteractive
work="$(mktemp -d)"
src_list=/etc/apt/sources.list.d/zz-vabaxos-debian-patched-src.list
cleanup() {
    rm -f "$src_list"
    rm -rf "$work"
}
trap cleanup EXIT

# Sources for the deb entries (one-line and deb822 files).
cat /etc/apt/sources.list /etc/apt/sources.list.d/*.list 2>/dev/null \
    | sed -n 's/^deb \(.*\)$/deb-src \1/p' > "$src_list"
for f in /etc/apt/sources.list.d/*.sources; do
    [ -f "$f" ] || continue
    case "$f" in */zz-src-*) continue ;; esac
    sed 's/^Types:.*/Types: deb-src/' "$f" > "/etc/apt/sources.list.d/zz-src-$(basename "$f")"
done
apt-get update -q >&2

# The version to rebuild: the installed one, or the newest APT knows.
target_version() {
    if [ "$INSTALLED" = true ]; then
        dpkg-query -W -f '${source:Version}' "$2"
        return
    fi
    best=""
    for v in $(apt-cache showsrc --only-source "$1" | sed -n 's/^Version: //p'); do
        if [ -z "$best" ] || dpkg --compare-versions "$v" gt "$best"; then
            best="$v"
        fi
    done
    echo "$best"
}

if [ "$PRINT" = true ]; then
    for dir in "$top"/*/; do
        [ -f "$dir/series" ] || continue
        source="$(basename "$dir")"
        first="$(grep -v '^#' "$dir/packages" | grep -v '^$' | head -n 1)"
        echo "$source $(target_version "$source" "$first")"
    done
    exit 0
fi

dpkg-query -W -f '${Package}\n' | sort > "$work/before"
apt-get install -y -q --no-install-recommends dpkg-dev build-essential fakeroot

# The date of the changelog entry: SOURCE_DATE_EPOCH when set (live-build
# sets it, so the ISO's packages have the same timestamps in every build),
# otherwise now.
stamp="$(date -u -R -d "@${SOURCE_DATE_EPOCH:-$(date +%s)}")"

for dir in "$top"/*/; do
    [ -f "$dir/series" ] || continue
    source="$(basename "$dir")"
    first="$(grep -v '^#' "$dir/packages" | grep -v '^$' | head -n 1)"
    version="$(target_version "$source" "$first")"
    [ -n "$version" ] || { echo "build-debian-patched: no source of $source" >&2; exit 1; }
    new="$version+0vabaxos1"
    echo "build-debian-patched: $source $version -> $new"

    mkdir -p "$work/$source"
    (cd "$work/$source" && apt-get source -q --only-source "$source=$version")
    tree="$(find "$work/$source" -mindepth 1 -maxdepth 1 -type d | head -n 1)"

    while read -r patch; do
        case "$patch" in ''|'#'*) continue ;; esac
        cp "$dir/$patch" "$tree/debian/patches/$patch"
        echo "$patch" >> "$tree/debian/patches/series"
    done < "$dir/series"

    {
        printf '%s (%s) %s; urgency=medium\n\n' "$source" "$new" \
            "$(dpkg-parsechangelog -l "$tree/debian/changelog" -S Distribution)"
        printf '  * VabaxOS (ADR-0026): %s.\n\n' \
            "$(grep -v '^#' "$dir/series" | grep -v '^$' | paste -sd, - | sed 's/,/, /g')"
        printf ' -- VabaxOS <https://github.com/Vabax-dev/VabaxOS>  %s\n\n' "$stamp"
        cat "$tree/debian/changelog"
    } > "$work/changelog"
    mv "$work/changelog" "$tree/debian/changelog"

    apt-get build-dep -y -q "$tree"
    (cd "$tree" && DEB_BUILD_OPTIONS="nocheck nodoc parallel=$(nproc)" \
        dpkg-buildpackage -b -uc -us)

    if [ -n "$OUT" ]; then
        mkdir -p "$OUT"
        find "$work/$source" -maxdepth 1 -name '*.deb' ! -name '*-dbgsym_*' -exec cp {} "$OUT/" \;
    fi
    debs=""
    while read -r package; do
        case "$package" in ''|'#'*) continue ;; esac
        deb="$(find "$work/$source" -maxdepth 1 -name "${package}_*.deb" | head -n 1)"
        [ -n "$deb" ] || { echo "build-debian-patched: $package was not built" >&2; exit 1; }
        if dpkg-query -W -f '${Status}' "$package" 2>/dev/null | grep -q 'ok installed'; then
            debs="$debs $deb"
        fi
    done < "$dir/packages"
    if [ "$INSTALL" = true ] && [ -n "$debs" ]; then
        # shellcheck disable=SC2086
        dpkg -i $debs
    fi
done

# Remove what the builds installed, and the extra sources.
dpkg-query -W -f '${Package}\n' | sort > "$work/after"
added="$(comm -13 "$work/before" "$work/after")"
if [ -n "$added" ]; then
    # shellcheck disable=SC2086
    apt-get purge -y -q $added
fi
rm -f "$src_list" /etc/apt/sources.list.d/zz-src-*.sources
apt-get update -q
