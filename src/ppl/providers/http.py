"""Shared HTTP POST for PPL model adapters (no vendor SDKs)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from ..production_runtime import PPLRuntimeError, RuntimeErrorCode


def map_http_status(status: int, body: str) -> PPLRuntimeError:
    snippet = (body or "")[:400]
    if status in {401}:
        return PPLRuntimeError(RuntimeErrorCode.AUTHENTICATION_ERROR, snippet or "authentication failed", retryable=False)
    if status in {403}:
        return PPLRuntimeError(RuntimeErrorCode.AUTHORIZATION_ERROR, snippet or "authorization failed", retryable=False)
    if status == 429:
        return PPLRuntimeError(RuntimeErrorCode.RATE_LIMIT_ERROR, snippet or "rate limited", retryable=True)
    if status in {408, 504}:
        return PPLRuntimeError(RuntimeErrorCode.TIMEOUT_ERROR, snippet or "timeout", retryable=True)
    if 500 <= status <= 599:
        return PPLRuntimeError(RuntimeErrorCode.TRANSIENT_ERROR, snippet or f"HTTP {status}", retryable=True)
    return PPLRuntimeError(RuntimeErrorCode.PROVIDER_ERROR, snippet or f"HTTP {status}", retryable=False)


def post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float = 60.0,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    merged = {"Content-Type": "application/json", **headers}
    req = urllib.request.Request(url, data=body, headers=merged, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        raise map_http_status(exc.code, err_body) from exc
    except TimeoutError as exc:
        raise PPLRuntimeError(RuntimeErrorCode.TIMEOUT_ERROR, str(exc), retryable=True) from exc
    except urllib.error.URLError as exc:
        raise PPLRuntimeError(RuntimeErrorCode.NETWORK_ERROR, str(exc.reason or exc), retryable=True) from exc
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PPLRuntimeError(RuntimeErrorCode.PROVIDER_ERROR, f"Non-JSON response: {raw[:200]}", retryable=False) from exc
    if not isinstance(parsed, dict):
        raise PPLRuntimeError(RuntimeErrorCode.PROVIDER_ERROR, "Provider JSON must be an object", retryable=False)
    return parsed
