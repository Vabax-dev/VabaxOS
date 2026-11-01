# SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""VabaxOS sounds: a short sound instead of the kind of control.

An Orca user extension (Orca 51 and later). Before Orca speaks, it looks
at the control the speech is about: if it is a button, a link, a check
box or another control with a VabaxOS sound, and the text contains the
name of that kind exactly as AT-SPI says it ("pulsante", "collegamento"),
the name is taken out and the sound plays instead. Nothing else changes:
if the name is not found, Orca speaks as always, so no information is
lost.

Installed and approved by the program vabaxos-orca-sounds, on the user's
request; the sounds are in /usr/share/vabaxos/orca-sounds.
"""

import os
import re

try:
    from orca.extension import Extension, SpeechOutputResult, get_translation
    _ = get_translation(__file__).gettext
except ImportError:          # outside Orca: the tests use strip_role() alone
    Extension, SpeechOutputResult = object, None

    def _(text):
        return text

SOUNDS = os.environ.get("VABAXOS_ORCA_SOUNDS", "/usr/share/vabaxos/orca-sounds")
# AT-SPI role names (Atspi.role_get_name, spaces as dashes, as Orca's own
# sound icons) that have a sound.
ROLES = ("push-button", "toggle-button", "link", "check-box", "radio-button", "combo-box", "menu",
         "page-tab", "entry", "password-text", "slider", "spin-button", "check-menu-item", "radio-menu-item",
         "switch")


def strip_role(text, role_key, role_name, sounds=SOUNDS):
    """(text without the role name, sound file) or None.

    role_key: the AT-SPI role name with dashes, role_name: the localized
    name as Orca speaks it."""
    if not text or not role_name or role_key not in ROLES:
        return None
    sound = os.path.join(sounds, role_key + ".wav")
    if not os.path.isfile(sound):
        return None
    pattern = re.compile(r"(?<!\w)" + re.escape(role_name.strip()) + r"(?!\w)", re.IGNORECASE)
    if not pattern.search(text):
        return None
    rest = pattern.sub("", text, count=1)
    rest = re.sub(r"\s+([,.;:])", r"\1", rest)
    rest = re.sub(r"^[\s,.;:]+|[\s,;:]+$", "", rest)
    rest = re.sub(r"\s{2,}", " ", rest)
    return rest, sound


def role_of(obj):
    """(role key, localized role name) of an AT-SPI object, or (None, None)."""
    try:
        import gi
        gi.require_version("Atspi", "2.0")
        from gi.repository import Atspi
        role = obj.get_role()
        return Atspi.role_get_name(role).replace(" ", "-"), obj.get_localized_role_name()
    except Exception:  # noqa: BLE001 - a dead object: speak as always
        return None, None


class VabaxosSounds(Extension):
    GROUP_LABEL = _("VabaxOS sounds")
    DESCRIPTION = _("A short sound instead of the names of buttons, links, check boxes and other controls.")
    VERSION = "1.0"
    ORGANIZATION = "VabaxOS"
    COPYRIGHT = "2026 Vabax and VabaxOS contributors"
    WEBSITE = "https://github.com/Vabax-dev/VabaxOS"

    def on_speech_output(self, output):
        if output.obj is None:
            return None
        role_key, role_name = role_of(output.obj)
        found = strip_role(output.text, role_key, role_name)
        if found is None:
            return None
        text, sound = found
        self.controller.play_sound_file_internal(sound)
        if not text:
            return SpeechOutputResult.consume_output()
        return SpeechOutputResult.replace(text)
