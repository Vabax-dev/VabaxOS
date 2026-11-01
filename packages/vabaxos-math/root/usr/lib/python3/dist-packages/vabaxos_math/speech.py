"""Formulas said in words, in Italian or English.

Orca speaks math poorly, and MathCAT (NVDA's engine) is not in Orca: so
VabaxOS turns a copied formula into a sentence. LaTeX, MathML (as in web
pages and LibreOffice) and plain writing (x^2, sqrt(x), a/b) are read:

    \\frac{a+b}{2}          frazione: a più b, fratto 2, fine frazione
    x^2 + y_1               x al quadrato più y con indice 1
    \\sqrt[3]{8}             radice cubica di 8
    \\sum_{i=1}^{n} i        sommatoria per i uguale a 1 fino a n di i
"""

import re
import xml.etree.ElementTree as ET

WORDS = {
    "it": {
        "+": "più", "-": "meno", "−": "meno", "*": "per", "×": "per", "·": "per", "/": "diviso", ":": "diviso",
        "÷": "diviso", "=": "uguale a", "<": "minore di", ">": "maggiore di", "≤": "minore o uguale a",
        "≥": "maggiore o uguale a", "≠": "diverso da", "±": "più o meno", "(": "aperta parentesi",
        ")": "chiusa parentesi", "[": "aperta quadra", "]": "chiusa quadra", "{": "aperta graffa",
        "}": "chiusa graffa", ",": "virgola", "!": "fattoriale", "%": "per cento", "∞": "infinito",
        "→": "che tende a", "'": "primo", "|": "valore assoluto",
        "frac": "frazione: {0}, fratto {1}, fine frazione", "frac_simple": "{0} fratto {1}",
        "square": "{0} al quadrato", "cube": "{0} al cubo", "power": "{0} elevato a {1}",
        "power_long": "{0} elevato a {1}, fine esponente", "sub": "{0} con indice {1}",
        "sqrt": "radice quadrata di {0}", "cbrt": "radice cubica di {0}", "root": "radice {1}-esima di {0}",
        "sum": "sommatoria", "prod": "produttoria", "int": "integrale", "lim": "limite",
        "from_to": "{0} da {1} a {2} di", "for": "{0} per {1} di", "for_to": "{0} per {1} fino a {2} di",
        "sin": "seno di", "cos": "coseno di", "tan": "tangente di", "log": "logaritmo di",
        "ln": "logaritmo naturale di", "exp": "esponenziale di",
    },
    "en": {
        "+": "plus", "-": "minus", "−": "minus", "*": "times", "×": "times", "·": "times", "/": "divided by",
        ":": "divided by", "÷": "divided by", "=": "equals", "<": "less than", ">": "greater than",
        "≤": "less than or equal to", "≥": "greater than or equal to", "≠": "not equal to", "±": "plus or minus",
        "(": "open paren", ")": "close paren", "[": "open bracket", "]": "close bracket", "{": "open brace",
        "}": "close brace", ",": "comma", "!": "factorial", "%": "percent", "∞": "infinity", "→": "tends to",
        "'": "prime", "|": "absolute value",
        "frac": "fraction: {0}, over {1}, end fraction", "frac_simple": "{0} over {1}",
        "square": "{0} squared", "cube": "{0} cubed", "power": "{0} to the power {1}",
        "power_long": "{0} to the power {1}, end exponent", "sub": "{0} sub {1}",
        "sqrt": "square root of {0}", "cbrt": "cube root of {0}", "root": "{1}th root of {0}",
        "sum": "sum", "prod": "product", "int": "integral", "lim": "limit",
        "from_to": "{0} from {1} to {2} of", "for": "{0} as {1} of", "for_to": "{0} for {1} up to {2} of",
        "sin": "sine of", "cos": "cosine of", "tan": "tangent of", "log": "log of", "ln": "natural log of",
        "exp": "exponential of",
    },
}
GREEK = {
    "alpha": ("alfa", "alpha"), "beta": ("beta", "beta"), "gamma": ("gamma", "gamma"), "delta": ("delta", "delta"),
    "epsilon": ("epsilon", "epsilon"), "varepsilon": ("epsilon", "epsilon"), "theta": ("teta", "theta"),
    "lambda": ("lambda", "lambda"), "mu": ("mi", "mu"), "pi": ("pi greco", "pi"), "rho": ("ro", "rho"),
    "sigma": ("sigma", "sigma"), "tau": ("tau", "tau"), "phi": ("fi", "phi"), "varphi": ("fi", "phi"),
    "omega": ("omega", "omega"), "Delta": ("delta maiuscola", "capital delta"),
    "Sigma": ("sigma maiuscola", "capital sigma"), "Omega": ("omega maiuscola", "capital omega"),
    "infty": ("infinito", "infinity"), "to": ("che tende a", "tends to"), "cdot": None, "times": None,
    "le": None, "leq": None, "ge": None, "geq": None, "ne": None, "neq": None, "pm": None,
}
LATEX_SYMBOL = {"cdot": "·", "times": "×", "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "ne": "≠",
                "neq": "≠", "pm": "±", "infty": "∞", "to": "→", "div": "÷"}
BIG = {"sum": "sum", "prod": "prod", "int": "int", "lim": "lim"}
FUNCS = {"sin", "cos", "tan", "log", "ln", "exp"}


def language_words(language):
    return WORDS.get((language or "it")[:2], WORDS["en"])


# -- LaTeX and plain writing --------------------------------------------------

_TOKEN = re.compile(r"\\[A-Za-z]+|\\.|\d+(?:[.,]\d+)?|[A-Za-z]|\S")


class Parser:
    """A small LaTeX reader: groups, \\frac, \\sqrt, ^, _, big operators."""

    def __init__(self, text, language):
        text = re.sub(r"\bsqrt\s*\(", r"\\sqrt(", text)
        self.tokens = _TOKEN.findall(text.replace("\\left", "").replace("\\right", ""))
        self.pos = 0
        self.w = language_words(language)
        self.index = 0 if (language or "it")[:2] == "it" else 1

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self):
        token = self.peek()
        self.pos += 1
        return token

    def group(self):
        """A {group}, a (group) after \\sqrt, or one token."""
        token = self.peek()
        if token == "{":
            self.take()
            return self.sequence(stop="}")
        if token == "(":
            self.take()
            return self.sequence(stop=")")
        return self.atom()

    def sequence(self, stop=None):
        parts = []
        while self.peek() is not None and self.peek() != stop:
            parts.append(self.term())
        if stop is not None and self.peek() == stop:
            self.take()
        return " ".join(p for p in parts if p)

    def atom(self):
        token = self.take()
        if token is None:
            return ""
        if token == "{":
            return self.sequence(stop="}")
        if token.startswith("\\"):
            return self.command(token[1:])
        if token in self.w and len(token) == 1:
            return self.w[token]
        return token.replace(".", ",") if self.index == 0 and token[0].isdigit() else token

    def command(self, name):
        w = self.w
        if name == "frac":
            top, bottom = self.group(), self.group()
            simple = len(top.split()) == 1 and len(bottom.split()) == 1
            return w["frac_simple" if simple else "frac"].format(top, bottom)
        if name == "sqrt":
            degree = None
            if self.peek() == "[":
                self.take()
                degree = self.sequence(stop="]")
            body = self.group()
            if degree in (None, "2"):
                return w["sqrt"].format(body)
            if degree == "3":
                return w["cbrt"].format(body)
            return w["root"].format(body, degree)
        if name in BIG:
            low = high = None
            while self.peek() in ("_", "^"):
                mark = self.take()
                if mark == "_":
                    low = self.group()
                else:
                    high = self.group()
            word = w[BIG[name]]
            if low and high:
                key = "from_to" if name == "int" else "for_to"
                return w[key].format(word, low, high)
            if low:
                return w["for"].format(word, low)
            return word + (" " + ("di" if self.index == 0 else "of"))
        if name in FUNCS:
            return w[name]
        if name in LATEX_SYMBOL:
            return w.get(LATEX_SYMBOL[name], LATEX_SYMBOL[name])
        if name in GREEK and GREEK[name]:
            return GREEK[name][self.index]
        if name in ("left", "right", ",", ";", "quad", "qquad", " "):
            return ""
        return name

    def term(self):
        base = self.atom()
        while self.peek() in ("^", "_"):
            mark = self.take()
            part = self.group()
            if mark == "_":
                base = self.w["sub"].format(base, part)
            elif part == "2":
                base = self.w["square"].format(base)
            elif part == "3":
                base = self.w["cube"].format(base)
            elif len(part.split()) == 1:
                base = self.w["power"].format(base, part)
            else:
                base = self.w["power_long"].format(base, part)
        return base


def from_latex(text, language="it"):
    text = text.strip().strip("$").strip()
    text = re.sub(r"^\\\[|\\\]$|^\\\(|\\\)$", "", text).strip()
    return _tidy(Parser(text, language).sequence())


# -- MathML ---------------------------------------------------------------------

def _local(tag):
    return tag.rsplit("}", 1)[-1]


def from_mathml(text, language="it"):
    root = ET.fromstring(text)
    w = language_words(language)
    return _tidy(_mathml(root, w, language))


def _mathml(node, w, language):
    tag = _local(node.tag)
    kids = list(node)
    say = [_mathml(k, w, language) for k in kids]
    if tag in ("mi", "mn", "mtext"):
        value = (node.text or "").strip()
        if tag == "mn" and (language or "it")[:2] == "it":
            value = value.replace(".", ",")
        for name, words in GREEK.items():
            if words and value == {"alpha": "α", "beta": "β", "pi": "π", "theta": "θ", "lambda": "λ",
                                   "sigma": "σ", "mu": "μ", "omega": "ω"}.get(name):
                return words[0 if (language or "it")[:2] == "it" else 1]
        return value
    if tag == "mo":
        value = (node.text or "").strip()
        return {"∑": w["sum"], "∏": w["prod"], "∫": w["int"]}.get(value, w.get(value, value))
    if tag == "mfrac" and len(say) == 2:
        simple = len(say[0].split()) == 1 and len(say[1].split()) == 1
        return w["frac_simple" if simple else "frac"].format(*say)
    if tag == "msqrt":
        return w["sqrt"].format(" ".join(say))
    if tag == "mroot" and len(say) == 2:
        return w["cbrt"].format(say[0]) if say[1] == "3" else w["root"].format(say[0], say[1])
    if tag == "msup" and len(say) == 2:
        if say[1] == "2":
            return w["square"].format(say[0])
        if say[1] == "3":
            return w["cube"].format(say[0])
        return w["power" if len(say[1].split()) == 1 else "power_long"].format(*say)
    if tag == "msub" and len(say) == 2:
        return w["sub"].format(*say)
    if tag in ("munderover", "msubsup") and len(say) == 3:
        key = "from_to" if say[0] == w["int"] else "for_to"
        return w[key].format(*say)
    if tag in ("munder",) and len(say) == 2:
        return w["for"].format(*say)
    if tag == "mfenced":
        return f"{w['(']} {' '.join(say)} {w[')']}"
    return " ".join(s for s in say if s)


# -- any formula --------------------------------------------------------------

def _tidy(text):
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+,", ",", text)


def say(text, language="it"):
    """A formula in words: MathML if it looks like it, else LaTeX or plain."""
    text = (text or "").strip()
    if not text:
        return ""
    if text.startswith("<"):
        try:
            return from_mathml(text, language)
        except ET.ParseError:
            pass
    return from_latex(text, language)
