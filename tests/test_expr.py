from pathlib import Path

import pytest

from ppl.expr import evaluate, parse_expr
from ppl.provider import public_config, test_provider


ROOT = Path(__file__).resolve().parents[1]


def test_expr_arithmetic_and_logic():
    ctx = {"calc": {"a": 10, "b": 3, "active": True}}
    assert evaluate("calc.a + calc.b", ctx) == 13
    assert evaluate("calc.a >= 8 AND calc.active == TRUE", ctx) is True
    assert evaluate('"hello " + "world"', ctx) == "hello world"


def test_expr_parse_roundtrip():
    expr = parse_expr("a + b * 2")
    assert expr.kind == "binary"
    restored = expr.to_dict()
    assert evaluate(restored, {"a": 1, "b": 2}) == 5


def test_provider_public_config():
    cfg = public_config()
    assert cfg["provider"] == "local"
    assert "supported" in cfg


def test_provider_test_local():
    result = test_provider()
    assert result["ok"] is True
    assert "category" in result["output"]
