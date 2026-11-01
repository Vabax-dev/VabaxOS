"""Documents for the VabaxOS reader: text out of a file, split into
paragraphs and sentences, and the reading position of each file.

Formats: plain text and Markdown, PDF (pdftotext of poppler-utils), Word
(.docx, python3-docx), EPUB (python3-ebooklib), HTML and saved web pages,
OpenDocument text (.odt, LibreOffice), RTF, DAISY books with text (DAISY 3
.xml, DAISY 2.02 ncc.html), and images and scanned PDFs through text
recognition (tesseract, Italian and English). Only Debian packages.

Headings (chapters, sections) are kept with their level, for the table of
contents of the reader: read_structure() gives paragraphs and headings.
"""

import hashlib
import html.parser
import json
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

IMAGES = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp")
SUPPORTED = (".txt", ".md", ".pdf", ".docx", ".epub", ".html", ".htm", ".xhtml", ".odt", ".rtf",
             ".xml") + IMAGES
OCR_LANGUAGES = "ita+eng"


class NeedsOCR(ValueError):
    """The document is made of images: its text must be recognized first,
    which takes a few seconds a page (read_paragraphs(path, ocr=True))."""


def ocr_image(path):
    result = subprocess.run(["tesseract", path, "-", "-l", OCR_LANGUAGES], capture_output=True, check=False)
    if result.returncode != 0:
        raise ValueError("the text could not be recognized")
    return result.stdout.decode("utf-8", "replace")


def ocr_pdf(path):
    """Each page as an image at 300 dpi, then tesseract."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", "300", "-png", path, os.path.join(tmp, "page")],
                       capture_output=True, check=True)
        pages = sorted(n for n in os.listdir(tmp) if n.endswith(".png"))
        return "\n\n".join(ocr_image(os.path.join(tmp, name)) for name in pages)


class _HTMLText(html.parser.HTMLParser):
    """Paragraphs of an HTML page: block elements end a paragraph."""

    BLOCKS = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "br", "tr", "blockquote", "section"}

    HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}

    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.headings = []    # (paragraph index, level, title)
        self.current = []
        self.skip = 0
        self.level = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "head", "nav"):
            self.skip += 1
        elif tag in self.BLOCKS:
            self._end()
            self.level = self.HEADINGS.get(tag, 0)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "head", "nav"):
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCKS:
            self._end()

    def handle_data(self, data):
        if not self.skip:
            self.current.append(data)

    def _end(self):
        text = " ".join("".join(self.current).split())
        if text:
            if self.level:
                self.headings.append((len(self.paragraphs), self.level, text))
            self.paragraphs.append(text)
        self.current = []
        self.level = 0

    def close(self):
        super().close()
        self._end()


def html_structure(markup):
    parser = _HTMLText()
    parser.feed(markup)
    parser.close()
    return parser.paragraphs, parser.headings


def html_paragraphs(markup):
    return html_structure(markup)[0]


def markdown_structure(text):
    """Paragraphs of Markdown or plain text; lines starting with # are
    headings."""
    paragraphs, headings = [], []
    for paragraph in text_paragraphs(re.sub(r"(?m)^(#{1,6}\s.*)$", "\n\\1\n", text)):
        match = re.match(r"^(#{1,6})\s+(.*)$", paragraph)
        if match:
            headings.append((len(paragraphs), len(match.group(1)), match.group(2).strip()))
            paragraphs.append(match.group(2).strip())
        else:
            paragraphs.append(paragraph)
    return paragraphs, headings


_ODF = {"text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0"}


def odt_structure(path):
    """OpenDocument text: text:h (with its outline level) and text:p, in
    the order of the document, also inside lists and tables."""
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("content.xml"))
    paragraphs, headings = [], []
    heading_tag = f"{{{_ODF['text']}}}h"
    paragraph_tag = f"{{{_ODF['text']}}}p"
    for node in root.iter():
        if node.tag not in (heading_tag, paragraph_tag):
            continue
        text = " ".join("".join(node.itertext()).split())
        if not text:
            continue
        if node.tag == heading_tag:
            level = int(node.get(f"{{{_ODF['text']}}}outline-level", "1") or 1)
            headings.append((len(paragraphs), level, text))
        paragraphs.append(text)
    return paragraphs, headings


def rtf_text(data):
    """The text of an RTF file: control words out, \\par as a new line,
    \\'hh and \\uN characters kept; tables of fonts, colours, styles out."""
    data = re.sub(r"\{\\\*[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", "", data)
    for group in ("fonttbl", "colortbl", "stylesheet", "info", "listtable", "listoverridetable"):
        data = re.sub(r"\{\\" + group + r"(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}", "", data)
    out = []
    i = 0
    while i < len(data):
        char = data[i]
        if char in "{}":
            i += 1
            continue
        if char != "\\":
            if char not in "\r\n":
                out.append(char)
            i += 1
            continue
        match = re.match(r"\\(?:'([0-9a-fA-F]{2})|u(-?\d+)\??|([a-zA-Z]+)(-?\d+)? ?|(.))", data[i:])
        if not match:
            i += 1
            continue
        hexa, uni, word, _num, other = match.groups()
        if hexa:
            out.append(bytes([int(hexa, 16)]).decode("cp1252", "replace"))
        elif uni:
            out.append(chr(int(uni) % 65536))
        elif word in ("par", "line", "sect", "page"):
            out.append("\n\n" if word != "line" else "\n")
        elif word == "tab":
            out.append("\t")
        elif other in ("\\", "{", "}"):
            out.append(other)
        i += match.end()
    return "".join(out)


def daisy_structure(path):
    """A DAISY 3 book (DTBook .xml): levels and headings, paragraphs."""
    root = ET.parse(path).getroot()
    if not root.tag.endswith("dtbook"):
        raise ValueError("this XML file is not a DAISY book")
    paragraphs, headings = [], []
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "hd"):
            text = " ".join("".join(node.itertext()).split())
            if text:
                level = int(tag[1]) if tag[0] == "h" and tag[1:].isdigit() else 6
                headings.append((len(paragraphs), level, text))
                paragraphs.append(text)
        elif tag in ("p", "li", "dd", "dt", "caption"):
            text = " ".join("".join(node.itertext()).split())
            if text:
                paragraphs.append(text)
    return paragraphs, headings


def text_paragraphs(text):
    """Blank lines separate paragraphs; single line breaks inside a
    paragraph (as in PDF and wrapped text) are joined."""
    paragraphs = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\f", "\n\n")):
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        joined = ""
        for line in lines:
            if joined.endswith("-") and line[:1].islower():
                joined = joined[:-1] + line  # a word cut at the end of a line
            else:
                joined = f"{joined} {line}" if joined else line
        paragraphs.append(joined)
    return paragraphs


def read_paragraphs(path, ocr=False):
    """The paragraphs of a document, or raises ValueError with a message.
    Images and scanned PDFs raise NeedsOCR unless ocr is true."""
    return read_structure(path, ocr)[0]


def read_structure(path, ocr=False):
    """(paragraphs, headings) of a document; headings are (paragraph index,
    level, title)."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".odt":
        return odt_structure(path)
    if ext == ".rtf":
        with open(path, encoding="latin-1") as f:
            return text_paragraphs(rtf_text(f.read())), []
    if ext == ".xml":
        return daisy_structure(path)
    if ext == ".md" or ext in (".txt", ""):
        with open(path, "rb") as f:
            data = f.read()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
        return markdown_structure(text) if ext == ".md" else (text_paragraphs(text), [])
    if ext in (".html", ".htm", ".xhtml"):
        with open(path, encoding="utf-8", errors="replace") as f:
            return html_structure(f.read())
    if ext == ".docx":
        import docx
        document = docx.Document(path)
        paragraphs, headings = [], []
        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            style = (paragraph.style.name if paragraph.style is not None else "") or ""
            match = re.match(r"^(?:Heading|Titolo|Title)\s*(\d?)$", style)
            if match:
                headings.append((len(paragraphs), int(match.group(1) or 1), text))
            paragraphs.append(text)
        return paragraphs, headings
    if ext == ".epub":
        import ebooklib
        from ebooklib import epub
        book = epub.read_epub(path, {"ignore_ncx": True})
        paragraphs, headings = [], []
        # The reading order of the book (spine), without its table of contents.
        for item_id, _linear in book.spine:
            item = book.get_item_with_id(item_id)
            if item is None or item.get_type() != ebooklib.ITEM_DOCUMENT or "nav" in (item.get_name() or ""):
                continue
            more, more_headings = html_structure(item.get_content().decode("utf-8", "replace"))
            headings += [(index + len(paragraphs), level, title) for index, level, title in more_headings]
            paragraphs += more
        return paragraphs, headings
    return _read_paragraphs_only(path, ext, ocr), []


def _read_paragraphs_only(path, ext, ocr):
    """Images and PDF: text without headings."""
    if ext in IMAGES:
        if not ocr:
            raise NeedsOCR("the text of the image must be recognized")
        return text_paragraphs(ocr_image(path))
    if ext == ".pdf":
        result = subprocess.run(["pdftotext", "-enc", "UTF-8", path, "-"], capture_output=True, check=False)
        if result.returncode != 0:
            raise ValueError("the PDF cannot be read")
        paragraphs = text_paragraphs(result.stdout.decode("utf-8", "replace"))
        if not paragraphs:
            if not ocr:
                raise NeedsOCR("the PDF has no text: it may be scanned images")
            paragraphs = text_paragraphs(ocr_pdf(path))
        return paragraphs
    raise ValueError("this kind of file is not supported")


_SENTENCE_END = re.compile(r"(?:(?<=[.!?…])|(?<=[.!?…][\"”’»)]))\s+(?=[\"“«(]*[A-ZÀ-ÖØ-Þ0-9])")


def sentences(paragraph):
    """Sentences of a paragraph. Short abbreviations (Sig., p. es.) do not
    end a sentence."""
    parts = []
    for piece in _SENTENCE_END.split(paragraph):
        piece = piece.strip()
        if not piece:
            continue
        if parts and re.search(r"\b(\w{1,3}|[A-Z])\.$", parts[-1]) and len(parts[-1]) < 12:
            parts[-1] = f"{parts[-1]} {piece}"
        else:
            parts.append(piece)
    return parts or [paragraph]


class Document:
    """A document as a list of sentences, each with its paragraph and its
    position in the text shown on the screen."""

    def __init__(self, paragraphs, path="", headings=None):
        self.path = path
        self.paragraphs = paragraphs
        self.headings = headings or []
        self.sentences = []   # (paragraph index, start offset, end offset, text)
        text = []
        offset = 0
        for index, paragraph in enumerate(paragraphs):
            if text:
                text.append("\n\n")
                offset += 2
            start_of_paragraph = offset
            position = 0
            for sentence in sentences(paragraph):
                found = paragraph.find(sentence, position)
                if found < 0:
                    found = position
                start = start_of_paragraph + found
                self.sentences.append((index, start, start + len(sentence), sentence))
                position = found + len(sentence)
            text.append(paragraph)
            offset += len(paragraph)
        self.text = "".join(text)

    @classmethod
    def open(cls, path, ocr=False):
        paragraphs, headings = read_structure(path, ocr)
        document = cls(paragraphs, path)
        document.headings = headings
        return document

    def heading_sentence(self, heading):
        """The first sentence of a heading's paragraph."""
        paragraph = heading[0]
        for index, sentence in enumerate(self.sentences):
            if sentence[0] >= paragraph:
                return index
        return max(0, len(self.sentences) - 1)

    def next_heading(self, index, step):
        """The heading after (step=1) or before (step=-1) the sentence at
        index, or None."""
        if not self.headings or not self.sentences:
            return None
        paragraph = self.sentences[index][0]
        if step > 0:
            after = [h for h in self.headings if h[0] > paragraph]
            return after[0] if after else None
        before = [h for h in self.headings if h[0] < paragraph]
        return before[-1] if before else None

    def sentence_at(self, offset):
        for index, (_, start, end, _) in enumerate(self.sentences):
            if offset < end + 2:
                return index
        return max(0, len(self.sentences) - 1)

    def next_paragraph(self, index, step):
        """The first sentence of the next (step=1) or previous (step=-1)
        paragraph, from sentence index."""
        if not self.sentences:
            return 0
        paragraph = self.sentences[index][0] + step
        paragraph = max(0, min(paragraph, self.sentences[-1][0]))
        for i, (p, *_rest) in enumerate(self.sentences):
            if p == paragraph:
                return i
        return index


def state_file():
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "vabaxos-reader", "state.json")


class ReadingState:
    """Where each document was left, and its bookmarks."""

    def __init__(self, path=None):
        self.path = path or state_file()
        try:
            with open(self.path, encoding="utf-8") as f:
                self.data = json.load(f)
        except (OSError, ValueError):
            self.data = {}

    @staticmethod
    def key(document_path):
        return hashlib.sha1(os.path.abspath(document_path).encode("utf-8")).hexdigest()

    def position(self, document_path):
        return self.data.get(self.key(document_path), {}).get("position", 0)

    def set_position(self, document_path, index):
        self.data.setdefault(self.key(document_path), {})["position"] = index
        self.save()

    def bookmarks(self, document_path):
        return self.data.get(self.key(document_path), {}).get("bookmarks", [])

    def add_bookmark(self, document_path, index, label):
        entry = self.data.setdefault(self.key(document_path), {})
        marks = entry.setdefault("bookmarks", [])
        if not any(m["index"] == index for m in marks):
            marks.append({"index": index, "label": label})
            marks.sort(key=lambda m: m["index"])
        self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, self.path)
