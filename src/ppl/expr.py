"""Expression parser and evaluator for PPL deterministic operations."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class Expr:
    """Serializable expression AST."""
    kind: str
    value: Any = None
    left: Expr | None = None
    right: Expr | None = None
    op: str | None = None
    parts: list[Expr] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"kind": self.kind}
        if self.value is not None:
            out["value"] = self.value
        if self.left is not None:
            out["left"] = self.left.to_dict()
        if self.right is not None:
            out["right"] = self.right.to_dict()
        if self.op is not None:
            out["op"] = self.op
        if self.parts is not None:
            out["parts"] = [p.to_dict() for p in self.parts]
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Expr:
        return cls(
            kind=data["kind"],
            value=data.get("value"),
            left=cls.from_dict(data["left"]) if data.get("left") else None,
            right=cls.from_dict(data["right"]) if data.get("right") else None,
            op=data.get("op"),
            parts=[cls.from_dict(p) for p in data.get("parts") or []],
        )


class ExprParser:
    """Parse arithmetic, comparison, and boolean expressions."""

    _BINOPS = {"+", "-", "*", "/", "%", ">=", "<=", "==", "!=", ">", "<"}
    _WORD_OPS = {"AND", "OR", "NOT"}

    def __init__(self, text: str):
        self.text = text.strip()
        self.pos = 0

    def error(self, msg: str) -> None:
        raise SyntaxError(f"Invalid expression '{self.text}': {msg}")

    def parse(self) -> Expr:
        if not self.text:
            self.error("empty expression")
        expr = self._parse_or()
        self._skip_ws()
        if self.pos < len(self.text):
            self.error(f"unexpected trailing input at '{self.text[self.pos:]}'")
        return expr

    def _skip_ws(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def _peek_word(self) -> str | None:
        self._skip_ws()
        m = re.match(r"[A-Za-z_][A-Za-z0-9_.]*", self.text[self.pos :])
        return m.group(0) if m else None

    def _consume_word(self, word: str) -> bool:
        self._skip_ws()
        if self.text[self.pos : self.pos + len(word)].upper() == word:
            self.pos += len(word)
            return True
        return False

    def _parse_or(self) -> Expr:
        left = self._parse_and()
        parts = [left]
        while self._consume_word("OR"):
            parts.append(self._parse_and())
        if len(parts) == 1:
            return left
        return Expr("bool", op="OR", parts=parts)

    def _parse_and(self) -> Expr:
        left = self._parse_not()
        parts = [left]
        while self._consume_word("AND"):
            parts.append(self._parse_not())
        if len(parts) == 1:
            return left
        return Expr("bool", op="AND", parts=parts)

    def _parse_not(self) -> Expr:
        if self._consume_word("NOT"):
            return Expr("unary", op="NOT", left=self._parse_not())
        return self._parse_compare()

    def _parse_compare(self) -> Expr:
        left = self._parse_add()
        while True:
            self._skip_ws()
            for op in (">=", "<=", "==", "!=", ">", "<"):
                if self.text.startswith(op, self.pos):
                    self.pos += len(op)
                    right = self._parse_add()
                    left = Expr("compare", op=op, left=left, right=right)
                    break
            else:
                break
        return left

    def _parse_add(self) -> Expr:
        left = self._parse_mul()
        while True:
            self._skip_ws()
            if self.pos >= len(self.text) or self.text[self.pos] not in "+-":
                break
            op = self.text[self.pos]
            self.pos += 1
            right = self._parse_mul()
            left = Expr("binary", op=op, left=left, right=right)
        return left

    def _parse_mul(self) -> Expr:
        left = self._parse_unary()
        while True:
            self._skip_ws()
            if self.pos >= len(self.text) or self.text[self.pos] not in "*/%":
                break
            op = self.text[self.pos]
            self.pos += 1
            right = self._parse_unary()
            left = Expr("binary", op=op, left=left, right=right)
        return left

    def _parse_unary(self) -> Expr:
        self._skip_ws()
        if self.pos < len(self.text) and self.text[self.pos] in "+-":
            op = self.text[self.pos]
            self.pos += 1
            return Expr("unary", op=op, left=self._parse_unary())
        return self._parse_primary()

    def _parse_primary(self) -> Expr:
        self._skip_ws()
        if self.pos >= len(self.text):
            self.error("unexpected end")
        ch = self.text[self.pos]
        if ch == "(":
            self.pos += 1
            expr = self._parse_or()
            self._skip_ws()
            if self.pos >= len(self.text) or self.text[self.pos] != ")":
                self.error("missing ')'")
            self.pos += 1
            return expr
        if ch in "\"'":
            quote = ch
            self.pos += 1
            buf = []
            while self.pos < len(self.text):
                c = self.text[self.pos]
                if c == quote:
                    self.pos += 1
                    return Expr("literal", value="".join(buf))
                if c == "\\" and self.pos + 1 < len(self.text):
                    buf.append(self.text[self.pos + 1])
                    self.pos += 2
                    continue
                buf.append(c)
                self.pos += 1
            self.error("unterminated string")
        m = re.match(r"-?\d+(?:\.\d+)?", self.text[self.pos :])
        if m:
            raw = m.group(0)
            self.pos += len(raw)
            value: Any = int(raw) if "." not in raw else float(raw)
            return Expr("literal", value=value)
        word = self._peek_word()
        if word:
            upper = word.upper()
            if upper == "TRUE":
                self.pos += len(word)
                return Expr("literal", value=True)
            if upper == "FALSE":
                self.pos += len(word)
                return Expr("literal", value=False)
            self.pos += len(word)
            return Expr("path", value=word)
        self.error(f"unexpected character '{ch}'")
        raise AssertionError


def parse_expr(text: str) -> Expr:
    return ExprParser(text).parse()


def _resolve_path(name: str, context: dict[str, Any]) -> Any:
    cur: Any = context
    for part in name.split("."):
        if isinstance(cur, dict):
            if part not in cur:
                return ""
            cur = cur[part]
        else:
            return ""
    return cur


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return False
    return bool(value)


def _coerce_number(value: Any) -> float:
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except ValueError:
        return 0.0


def evaluate(expr: Expr | dict[str, Any] | str, context: dict[str, Any]) -> Any:
    if isinstance(expr, str):
        return evaluate(parse_expr(expr), context)
    if isinstance(expr, dict):
        return evaluate(Expr.from_dict(expr), context)
    if expr.kind == "literal":
        return expr.value
    if expr.kind == "path":
        return _resolve_path(str(expr.value), context)
    if expr.kind == "unary":
        val = evaluate(expr.left, context)
        if expr.op == "NOT":
            return not _truthy(val)
        if expr.op == "-":
            return -_coerce_number(val)
        if expr.op == "+":
            return _coerce_number(val)
        raise ValueError(f"unknown unary op {expr.op}")
    if expr.kind == "binary":
        left = evaluate(expr.left, context)
        right = evaluate(expr.right, context)
        if expr.op == "+":
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            if isinstance(left, int) and isinstance(right, int):
                return left + right
            return _coerce_number(left) + _coerce_number(right)
        if expr.op == "-":
            return _coerce_number(left) - _coerce_number(right)
        if expr.op == "*":
            return _coerce_number(left) * _coerce_number(right)
        if expr.op == "/":
            denom = _coerce_number(right)
            if denom == 0:
                raise ZeroDivisionError("division by zero")
            return _coerce_number(left) / denom
        if expr.op == "%":
            return int(_coerce_number(left)) % int(_coerce_number(right))
        raise ValueError(f"unknown binary op {expr.op}")
    if expr.kind == "compare":
        left = evaluate(expr.left, context)
        right = evaluate(expr.right, context)
        ops = {
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
        }
        return ops[expr.op](left, right)
    if expr.kind == "bool":
        parts = expr.parts or []
        if expr.op == "AND":
            return all(_truthy(evaluate(p, context)) for p in parts)
        if expr.op == "OR":
            return any(_truthy(evaluate(p, context)) for p in parts)
        raise ValueError(f"unknown bool op {expr.op}")
    raise ValueError(f"unknown expr kind {expr.kind}")


def evaluate_bool(expr: Expr | dict[str, Any] | str, context: dict[str, Any]) -> bool:
    return bool(evaluate(expr, context))
