"""AccessGram, a Telegram client made for Orca (MIT, GTK 4 and Python,
github.com/destructatron/AccessGram), downloaded on the user's request.

It is not in the ISO: it is young (0.1.0, "alpha"), in English only, and
its two sounds come without a stated licence. VabaxOS downloads one
version, fixed here, checks its whole content with SHA-256 and runs it
with Telethon from Debian (python3-telethon). Telegram asks every program
for an "API ID" and "API hash", which each user gets at my.telegram.org.

    install(opener)    downloads, checks, unpacks, adds the launcher
    installed(), remove(), launcher_path()
"""

import hashlib
import io
import os
import shutil
import urllib.request
import zipfile

COMMIT = "feb0d887026175da832ca0d5e6bbb6237725962c"     # 2026-03-29
# SHA-256 of every file (sorted path, NUL, content, NUL): the same whatever
# the compression of GitHub's archive.
TREE_SHA = "b5bbb947db4648359594f4f0f579685988256f5569923ddddd91f0550659a9d8"
URL = "https://codeload.github.com/destructatron/AccessGram/zip/" + COMMIT
USER_AGENT = "VabaxOS/1.0 (+https://github.com/Vabax-dev/VabaxOS)"
MY_TELEGRAM = "https://my.telegram.org"


class InstallError(RuntimeError):
    pass


def data_dir():
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "vabaxos", "accessgram")


def code_dir(folder=None):
    return os.path.join(folder or data_dir(), COMMIT[:12])


def launcher_path():
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "applications", "org.vabaxos.AccessGram.desktop")


def installed(folder=None):
    return os.path.exists(os.path.join(code_dir(folder), "accessgram", "__main__.py"))


def tree_hash(archive):
    """The SHA-256 of the files of a GitHub archive, without its top folder."""
    digest = hashlib.sha256()
    names = sorted(n for n in archive.namelist() if not n.endswith("/"))
    for name in names:
        relative = name.split("/", 1)[1] if "/" in name else name
        digest.update(relative.encode() + b"\0")
        digest.update(archive.read(name))
        digest.update(b"\0")
    return digest.hexdigest()


def launcher_text(folder=None):
    code = code_dir(folder)
    return ("[Desktop Entry]\nType=Application\nName=AccessGram\n"
            "Name[it]=AccessGram, Telegram per Orca\n"
            "Comment=Telegram, made for the screen reader\nComment[it]=Telegram, fatto per il lettore di schermo\n"
            f"Exec=env PYTHONPATH={code} python3 -m accessgram\n"
            "Icon=internet-chat-symbolic\nTerminal=false\nCategories=Network;InstantMessaging;\n"
            "Keywords=telegram;chat;messages;messaggi;\n")


def install(opener=urllib.request.urlopen, folder=None, expected=TREE_SHA):
    request = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
    with opener(request, timeout=60) as reply:
        data = reply.read()
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as error:
        raise InstallError("damaged") from error
    if tree_hash(archive) != expected:
        raise InstallError("damaged")
    target = code_dir(folder)
    partial = target + ".part"
    shutil.rmtree(partial, ignore_errors=True)
    for name in archive.namelist():
        if name.endswith("/") or "/" not in name:
            continue
        relative = os.path.normpath(name.split("/", 1)[1])
        if relative.startswith("..") or os.path.isabs(relative):
            raise InstallError("damaged")
        path = os.path.join(partial, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(archive.read(name))
    shutil.rmtree(target, ignore_errors=True)
    os.replace(partial, target)
    launcher = launcher_path()
    os.makedirs(os.path.dirname(launcher), exist_ok=True)
    with open(launcher, "w", encoding="utf-8") as f:
        f.write(launcher_text(folder))
    return target


def remove(folder=None):
    """Removes the program; the user's Telegram session and settings, kept
    by AccessGram in its own folders, stay unless removed by hand."""
    shutil.rmtree(folder or data_dir(), ignore_errors=True)
    try:
        os.remove(launcher_path())
    except OSError:
        pass
