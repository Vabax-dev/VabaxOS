"""A safe calculator: an expression as people write it, its value.

    3+4*2      3 + 4 × 2      2,5 * 4      2^10      radice(2)      sqrt 16
    20% di 150      sin(30)  (degrees)      pi * 2      (1+2)/3

Only numbers, + - * / ^ % and the functions below: no Python is run.
"""

import ast
import math
import operator
import re

FUNCTIONS = {
    "sqrt": math.sqrt, "radice": math.sqrt, "rad": math.sqrt,
    "sin": lambda x: math.sin(math.radians(x)), "sen": lambda x: math.sin(math.radians(x)),
    "cos": lambda x: math.cos(math.radians(x)), "tan": lambda x: math.tan(math.radians(x)),
    "tg": lambda x: math.tan(math.radians(x)),
    "log": math.log10, "ln": math.log, "abs": abs, "exp": math.exp,
}
CONSTANTS = {"pi": math.pi, "pigreco": math.pi, "π": math.pi, "e": math.e}
OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
             ast.Pow: operator.pow, ast.Mod: operator.mod, ast.USub: operator.neg, ast.UAdd: operator.pos}


class CalcError(ValueError):
    pass


def normalize(text):
    """People's writing as an expression: 2,5 -> 2.5, × and x -> *, ÷ and : -> /,
    ^ -> **, 20% di 150 -> 20/100*150, "radice di 2" -> radice(2)."""
    text = text.strip().lower()
    text = re.sub(r"(\d+(?:[.,]\d+)?)\s*%\s*(?:di|of)\s*", r"(\1)/100*", text)
    text = re.sub(r"(\d),(\d)", r"\1.\2", text)
    text = text.replace("×", "*").replace("·", "*").replace("÷", "/").replace("^", "**").replace(":", "/")
    text = re.sub(r"(?<=[\d)\s])x(?=[\s\d(])", "*", text)
    text = re.sub(r"\b(sqrt|radice|rad|sin|sen|cos|tan|tg|log|ln|abs|exp)\s+(?:di\s+|of\s+)?"
                  r"(\d+(?:\.\d+)?|pi|pigreco|e)\b", r"\1(\2)", text)
    text = re.sub(r"\b(sqrt|radice|rad|sin|sen|cos|tan|tg|log|ln|abs|exp)\s+(?:di|of)\s*\(", r"\1(", text)
    text = text.replace("π", "pi")
    text = re.sub(r"(\d)\s*\(", r"\1*(", text)
    return text


def evaluate(text):
    expression = normalize(text)
    if not expression:
        raise CalcError("empty")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise CalcError("not an expression") from error
    return _value(tree.body)


def _value(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name) and node.id in CONSTANTS:
        return CONSTANTS[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left, right = _value(node.left), _value(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise CalcError("too big")
        try:
            return OPERATORS[type(node.op)](left, right)
        except ZeroDivisionError as error:
            raise CalcError("division by zero") from error
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_value(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS \
            and len(node.args) == 1 and not node.keywords:
        try:
            return FUNCTIONS[node.func.id](_value(node.args[0]))
        except (ValueError, OverflowError) as error:
            raise CalcError("not defined") from error
    raise CalcError("not allowed")


def format_number(value, decimal=","):
    """10 significant digits, no trailing zeros, the decimal comma."""
    if isinstance(value, float) and (math.isinf(value) or math.isnan(value)):
        raise CalcError("not a number")
    if isinstance(value, int) or float(value).is_integer() and abs(value) < 1e15:
        return str(int(round(value)))
    text = f"{value:.10g}"
    if "e" in text:
        mantissa, exponent = text.split("e")
        text = f"{mantissa} × 10^{int(exponent)}"
    return text.replace(".", decimal)
