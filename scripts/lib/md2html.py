#!/usr/bin/env python3
"""Turns the user guides (docs/utente/*.md) into accessible HTML pages for
the VabaxOS help (package vabaxos-help), with the standard library only.

    md2html.py SOURCE_DIR OUTPUT_DIR

Handles what the guides use: headings, paragraphs, lists (also nested and
numbered), quotes, code blocks, inline code, bold and links (links to
other guides become links to their pages; other repository links go to
GitHub). Every page has a language, a title, a main landmark and a link
back to the index, so a screen reader can move through it by headings.
"""

import html
import os
import re
import sys

ORDER = ["menu-di-avvio", "benvenuto", "voce", "lettore-di-schermo", "configurazione", "desktop", "tasti", "menu-start",
         "lettore", "installazione", "aggiornamenti"]
REPO_URL = "https://github.com/Vabax-dev/VabaxOS/blob/main/"
STYLE = """body { font-family: "Atkinson Hyperlegible Next", sans-serif; font-size: 1.15rem;
  line-height: 1.6; max-width: 46rem; margin: 2rem auto; padding: 0 1rem;
  color: #0b1b3f; background: #fffdf8; }
a { color: #3a0fb0; } code, pre { font-family: "Adwaita Mono", monospace; }
pre { background: #f0ecff; padding: .8rem; overflow-x: auto; }
@media (prefers-color-scheme: dark) { body { color: #f4f4f4; background: #0b1b3f; }
  a { color: #ffe14d; } pre { background: #1d2b57; } }
"""


def inline(text, pages):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)

    def link(match):
        label, target = match.group(1), html.unescape(match.group(2))
        name = os.path.splitext(os.path.basename(target))[0]
        if target.endswith(".md") and name in pages and "/" not in target.lstrip("./"):
            href = name + ".html"
        elif target.startswith("http"):
            href = target
        else:
            href = REPO_URL + os.path.normpath(os.path.join("docs/utente", target))
        return f'<a href="{html.escape(href)}">{label}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)


def convert(markdown, pages):
    out, para, lists = [], [], []
    title = ""
    lines = markdown.split("\n")
    i = 0

    def close_para():
        if para:
            out.append("<p>" + inline(" ".join(para), pages) + "</p>")
            para.clear()

    def close_lists(level=0):
        while len(lists) > level:
            out.append(f"</li></{lists.pop()}>")

    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            close_para(); close_lists()
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
        elif re.match(r"^#{1,6} ", line):
            close_para(); close_lists()
            level = len(line) - len(line.lstrip("#"))
            text = line[level:].strip()
            if level == 1 and not title:
                title = text
            out.append(f"<h{level}>{inline(text, pages)}</h{level}>")
        elif re.match(r"^\s*([-*]|\d+\.) ", line):
            close_para()
            indent = len(line) - len(line.lstrip(" "))
            level = indent // 2 + 1
            kind = "ol" if re.match(r"^\s*\d+\.", line) else "ul"
            text = re.sub(r"^\s*([-*]|\d+\.) ", "", line)
            if len(lists) < level:
                out.append(f"<{kind}><li>")
                lists.append(kind)
            else:
                close_lists(level)
                out.append("</li><li>")
            out.append(inline(text, pages))
        elif line.startswith(">"):
            close_para(); close_lists()
            out.append("<blockquote><p>" + inline(line.lstrip("> "), pages) + "</p></blockquote>")
        elif not line.strip():
            close_para()
            if not (i + 1 < len(lines) and re.match(r"^\s*([-*]|\d+\.) ", lines[i + 1])):
                close_lists()
        elif lists and line.startswith(" "):
            out.append(" " + inline(line.strip(), pages))
        else:
            close_lists()
            para.append(line.strip())
        i += 1
    close_para(); close_lists()
    return title, "\n".join(out)


def page(title, body, index_link=True):
    back = '<nav><a href="index.html">Indice dell\'aiuto di VabaxOS</a></nav>\n' if index_link else ""
    return (f'<!DOCTYPE html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{html.escape(title)} - Aiuto di VabaxOS</title>\n<style>{STYLE}</style>\n</head>\n"
            f"<body>\n{back}<main>\n{body}\n</main>\n</body>\n</html>\n")


def main(source, output):
    pages = [os.path.splitext(n)[0] for n in os.listdir(source) if n.endswith(".md")]
    ordered = [p for p in ORDER if p in pages] + sorted(p for p in pages if p not in ORDER)
    os.makedirs(output, exist_ok=True)
    titles = {}
    for name in ordered:
        with open(os.path.join(source, name + ".md"), encoding="utf-8") as f:
            title, body = convert(f.read(), pages)
        titles[name] = title or name
        with open(os.path.join(output, name + ".html"), "w", encoding="utf-8") as f:
            f.write(page(titles[name], body))
    items = "\n".join(f'<li><a href="{n}.html">{html.escape(titles[n])}</a></li>' for n in ordered)
    body = ("<h1>Aiuto di VabaxOS</h1>\n<p>Le guide di VabaxOS, da leggere con Orca: "
            "in ogni pagina il tasto H passa da un titolo all'altro.</p>\n"
            f"<ul>\n{items}\n</ul>")
    with open(os.path.join(output, "index.html"), "w", encoding="utf-8") as f:
        f.write(page("Indice", body, index_link=False))
    print(f"{len(ordered)} guide in {output}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
