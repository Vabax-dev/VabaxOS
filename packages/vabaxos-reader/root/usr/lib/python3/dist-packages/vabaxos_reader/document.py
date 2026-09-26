"""Documents for the VabaxOS reader: text out of a file, split into
paragraphs and sentences, and the reading position of each file.

Formats: plain text and Markdown, PDF (pdftotext of poppler-utils), Word
(.docx, python3-docx), EPUB (python3-ebooklib), HTML, and images and
scanned PDFs through text recognition (tesseract, Italian and English).
Only Debian packages.
"""

import hashlib
import html.parser
import json
import os
import re
import subprocess
import tempfile

IMAGES = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp")
SUPPORTED = (".txt", ".md", ".pdf", ".docx", ".epub", ".html", ".htm") + IMAGES
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

    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.current = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "head"):
            self.skip += 1
        elif tag in self.BLOCKS:
            self._end()

    def handle_endtag(self, tag):
        if tag in ("script", "style", "head"):
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCKS:
            self._end()

    def handle_data(self, data):
        if not self.skip:
            self.current.append(data)

    def _end(self):
        text = " ".join("".join(self.current).split())
        if text:
            self.paragraphs.append(text)
        self.current = []

    def close(self):
        super().close()
        self._end()


def html_paragraphs(markup):
    parser = _HTMLText()
    parser.feed(markup)
    parser.close()
    return parser.paragraphs


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
    # A full path: a name such as "-x.pdf" must not look like an option to
    # pdftotext, pdftoppm or tesseract.
    path = os.path.abspath(path)
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGES:
        if not ocr:
            raise NeedsOCR("the text of the image must be recognized")
        return text_paragraphs(ocr_image(path))
    if ext in (".txt", ".md", ""):
        with open(path, "rb") as f:
            data = f.read()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
        return text_paragraphs(text)
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
    if ext == ".docx":
        import docx
        document = docx.Document(path)
        return [p.text.strip() for p in document.paragraphs if p.text.strip()]
    if ext == ".epub":
        import ebooklib
        from ebooklib import epub
        book = epub.read_epub(path, {"ignore_ncx": True})
        paragraphs = []
        # The reading order of the book (spine), without its table of contents.
        for item_id, _linear in book.spine:
            item = book.get_item_with_id(item_id)
            if item is None or item.get_type() != ebooklib.ITEM_DOCUMENT or "nav" in (item.get_name() or ""):
                continue
            paragraphs += html_paragraphs(item.get_content().decode("utf-8", "replace"))
        return paragraphs
    if ext in (".html", ".htm"):
        with open(path, encoding="utf-8", errors="replace") as f:
            return html_paragraphs(f.read())
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

    def __init__(self, paragraphs, path=""):
        self.path = path
        self.paragraphs = paragraphs
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
        return cls(read_paragraphs(path, ocr), path)

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
