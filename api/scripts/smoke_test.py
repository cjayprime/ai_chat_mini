"""Smoke test for the Meridian chatbot backend.

Run with:
    python scripts/smoke_test.py --url http://localhost:8000
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request
import json

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"


def request(url: str, method: str = "GET", body: dict | None = None, timeout: int = 30) -> tuple[int, str, float]:
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.monotonic() - start) * 1000
            return resp.status, resp.read().decode(), elapsed
    except urllib.error.HTTPError as e:
        elapsed = (time.monotonic() - start) * 1000
        return e.code, e.read().decode(), elapsed
    except urllib.error.URLError as e:
        elapsed = (time.monotonic() - start) * 1000
        return 0, str(e.reason), elapsed


def check(name: str, passed: bool, detail: str, ms: float) -> bool:
    tag = PASS if passed else FAIL
    print(f"  [{tag}] {name} ({ms:.0f}ms) -- {detail}")
    return passed


def main() -> None:
    parser = argparse.ArgumentParser(description="Meridian chatbot smoke test")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend base URL")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    print(f"\nSmoke testing: {base}\n")
    results: list[bool] = []

    # ── 1. Health check ──
    print("1. Health endpoint")
    status, body, ms = request(f"{base}/health")
    results.append(check("GET /health returns 200", status == 200, f"status={status}", ms))
    if status == 200:
        data = json.loads(body)
        results.append(check("MCP connected", data.get("mcp_connected") is True, f"mcp_connected={data.get('mcp_connected')}", ms))
        results.append(check("Tools loaded", data.get("tools_loaded", 0) == 8, f"tools_loaded={data.get('tools_loaded')}", ms))

    # ── 2. Product browsing (no auth needed) ──
    print("\n2. Product browsing")
    session_id = "smoke-test-001"
    status, body, ms = request(
        f"{base}/chat",
        method="POST",
        body={"session_id": session_id, "message": "What monitors do you have?", "history": []},
    )
    results.append(check("POST /chat returns 200", status == 200, f"status={status}", ms))
    if status == 200:
        data = json.loads(body)
        msg = data.get("message", "").lower()
        results.append(check("Response mentions monitors", "monitor" in msg, f"response_length={len(msg)}", ms))
        tools = [t["tool_name"] for t in data.get("tool_calls_made", [])]
        results.append(check(
            "Used product tool",
            any(t in tools for t in ["list_products", "search_products"]),
            f"tools_called={tools}",
            ms,
        ))

    # ── 3. Product search ──
    print("\n3. Product search")
    status, body, ms = request(
        f"{base}/chat",
        method="POST",
        body={"session_id": session_id, "message": "Search for laser printers", "history": []},
    )
    results.append(check("POST /chat returns 200", status == 200, f"status={status}", ms))
    if status == 200:
        data = json.loads(body)
        msg = data.get("message", "").lower()
        results.append(check("Response mentions printer", "printer" in msg or "pri-" in msg, f"response_length={len(msg)}", ms))

    # ── 4. Auth gate ──
    print("\n4. Auth gate")
    status, body, ms = request(
        f"{base}/chat",
        method="POST",
        body={"session_id": "smoke-test-002", "message": "Show me my orders", "history": []},
    )
    results.append(check("POST /chat returns 200", status == 200, f"status={status}", ms))
    if status == 200:
        data = json.loads(body)
        msg = data.get("message", "").lower()
        asks_for_auth = any(kw in msg for kw in ["email", "pin", "verify", "identity", "authenticate"])
        results.append(check("Bot asks for authentication", asks_for_auth, f"response_length={len(msg)}", ms))
        tools = [t["tool_name"] for t in data.get("tool_calls_made", [])]
        results.append(check("No order tools called without auth", "list_orders" not in tools, f"tools_called={tools}", ms))

    # ── 5. Input validation ──
    print("\n5. Input validation")
    status, body, ms = request(
        f"{base}/chat",
        method="POST",
        body={"session_id": "", "message": "hello", "history": []},
    )
    results.append(check("Empty session_id -> 422", status == 422, f"status={status}", ms))

    status, body, ms = request(
        f"{base}/chat",
        method="POST",
        body={"session_id": "test", "message": "", "history": []},
    )
    results.append(check("Empty message -> 422", status == 422, f"status={status}", ms))

    # ── Summary ──
    passed = sum(results)
    total = len(results)
    failed = total - passed
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} passed", end="")
    if failed:
        print(f", {failed} failed")
    else:
        print(" -- all clear!")
    print(f"{'=' * 50}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
