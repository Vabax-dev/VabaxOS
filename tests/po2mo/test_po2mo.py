#!/usr/bin/env python3
"""Tests for scripts/lib/po2mo.py, the .mo compiler used when msgfmt is
missing (as in CI): contexts, plural forms, fuzzy entries, and the same
catalog as msgfmt for every translation of the packages.

    python3 tests/po2mo/test_po2mo.py
"""

import gettext
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts", "lib"))

import po2mo  # noqa: E402

PO = r'''# A test.
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"

msgid "Hello"
msgstr "Ciao"

msgctxt "network"
msgid "connected"
msgstr "in uso"

msgid "connected"
msgstr "collegato"

msgid "{count} network"
msgid_plural "{count} networks"
msgstr[0] "{count} rete"
msgstr[1] "{count} reti"

#, fuzzy
msgid "Maybe"
msgstr "Forse"

msgid "Long "
"text"
msgstr "Testo "
"lungo"

msgid "Untranslated"
msgstr ""
'''


class Po2MoTest(unittest.TestCase):

    def compile(self, text):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder)
        po, mo = os.path.join(folder, "t.po"), os.path.join(folder, "t.mo")
        with open(po, "w", encoding="utf-8") as f:
            f.write(text)
        po2mo.write_mo(po2mo.parse(po), mo)
        with open(mo, "rb") as f:
            return gettext.GNUTranslations(f)

    def test_entries(self):
        t = self.compile(PO)
        self.assertEqual(t.gettext("Hello"), "Ciao")
        self.assertEqual(t.pgettext("network", "connected"), "in uso")
        self.assertEqual(t.gettext("connected"), "collegato")
        self.assertEqual(t.ngettext("{count} network", "{count} networks", 1), "{count} rete")
        self.assertEqual(t.ngettext("{count} network", "{count} networks", 5), "{count} reti")
        self.assertEqual(t.gettext("Maybe"), "Maybe", "fuzzy entries are left out")
        self.assertEqual(t.gettext("Long text"), "Testo lungo")
        self.assertEqual(t.gettext("Untranslated"), "Untranslated")

    @unittest.skipUnless(shutil.which("msgfmt"), "msgfmt (gettext) is not installed")
    def test_same_as_msgfmt(self):
        for po in sorted(glob.glob(os.path.join(REPO, "packages", "*", "po", "*.po"))):
            with tempfile.TemporaryDirectory() as folder:
                ours, theirs = os.path.join(folder, "ours.mo"), os.path.join(folder, "theirs.mo")
                po2mo.write_mo(po2mo.parse(po), ours)
                subprocess.run(["msgfmt", "-o", theirs, po], check=True)
                with open(ours, "rb") as a, open(theirs, "rb") as b:
                    mine, msgfmt = gettext.GNUTranslations(a)._catalog, gettext.GNUTranslations(b)._catalog
                mine.pop("", None)
                msgfmt.pop("", None)
                self.assertEqual(mine, msgfmt, po)


if __name__ == "__main__":
    unittest.main(verbosity=2)
