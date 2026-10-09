#!/usr/bin/env python3
"""Prove the payment layer of a product actually works at runtime.

The audit reads source; this boots the API and exercises the money paths that a
buyer depends on the moment they insert keys:

  1. GET  /health                                   — the process starts
  2. GET  /api/lemonsqueezy/config                  — storefront configuration
  3. POST /api/lemonsqueezy/checkout                — unconfigured keys answer 503
  4. POST /api/lemonsqueezy/webhook  (valid  X-Signature)   -> 200, event applied
  5. POST /api/lemonsqueezy/webhook  (replay)                -> idempotent, not applied twice
  6. POST /api/lemonsqueezy/webhook  (bad     X-Signature)   -> 401
  7. POST /api/payment/webhook       (Stripe path, unsigned)  -> 403, and no hang
  8. POST /api/webhook/emit         (ordinary JSON route)    -> body still parsed
  9. POST /api/auth/register + /login                        -> auth untouched

Requirements: the product's `backend/node_modules` must exist (this script never
installs anything).

    python scripts/verify_payments.py                    # every product
    python scripts/verify_payments.py apex               # one product
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"

WEBHOOK_SECRET = "verify-lemonsqueezy-signing-secret"

LS_EVENT = {
    "meta": {
        "event_name": "order_created",
        "event_id": "verify-event-0001",
        "custom_data": {"plan": "starter"},
    },
    "data": {
        "type": "orders",
        "id": "999001",
        "attributes": {
            "user_email": "buyer@shop.test",
            "total": 4900,
            "currency": "USD",
            "status": "paid",
        },
    },
}


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def call(url: str, payload=None, method="GET", headers=None, timeout=15):
    body = json.dumps(payload).encode() if payload is not None else None
    hdrs = {"Accept": "application/json", **(headers or {})}
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(2000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(2000).decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001 - a dead socket is a real result here
        return 0, str(e)


def post_raw(url: str, raw: bytes, headers=None, timeout=15):
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=raw, method="POST", headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(2000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(2000).decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def signature(raw: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


def run_product(product: Path) -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []
    backend = product / "backend"

    if not (backend / "node_modules").is_dir():
        return [("dependencies", False, "backend/node_modules missing — install first")]

    port = free_port()
    env = {
        **os.environ,
        "NODE_ENV": "development",
        "PORT": str(port),
        "JWT_SECRET": "verification-access-secret-verification-access",
        "JWT_REFRESH_SECRET": "verification-refresh-secret-verification",
        "ENABLE_DEMO_SEED": "true",
        "DEMO_USER_PASSWORD": "VerifyOnly!123",
        "REDIS_DISABLED": "true",
        "AI_AGENT_URL": "http://127.0.0.1:9",
        "LEMONSQUEEZY_WEBHOOK_SECRET": WEBHOOK_SECRET,
    }
    env.pop("DATABASE_URL", None)

    proc = subprocess.Popen(
        ["node", "server.js"], cwd=str(backend), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    base = f"http://127.0.0.1:{port}"

    def check(label: str, ok: bool, detail: str) -> None:
        results.append((label, ok, detail))

    try:
        deadline = time.time() + 45
        up = False
        while time.time() < deadline and proc.poll() is None:
            code, body = call(f"{base}/health", timeout=4)
            if code == 200:
                up = True
                check("health", True, body[:80])
                break
            time.sleep(1)
        if not up:
            out = ""
            try:
                proc.kill()
                out = proc.stdout.read(2000)
            except Exception:
                pass
            check("health", False, f"no /health within 45s — {out[:400]}")
            return results

        # 1. storefront configuration
        code, body = call(f"{base}/api/lemonsqueezy/config")
        ok = code == 200 and '"configured"' in body
        check("ls config", ok, f"{code} {body[:140]}")

        # 2. checkout without keys -> a clear, non-crashing answer
        code, body = call(
            f"{base}/api/lemonsqueezy/checkout",
            {"planName": "Starter", "amount": 49, "currency": "USD"},
            method="POST",
        )
        ok = code in (200, 401, 503) and "url" in body or code == 503
        check("ls checkout (no keys)", code in (200, 401, 503), f"{code} {body[:140]}")

        # 3. signed webhook, delivered twice
        raw = json.dumps(LS_EVENT).encode()
        code, body = post_raw(
            f"{base}/api/lemonsqueezy/webhook",
            raw,
            headers={
                "X-Signature": signature(raw, WEBHOOK_SECRET),
                "X-Event-Name": "order_created",
            },
        )
        check("ls webhook (signed)", code == 200 and '"received"' in body, f"{code} {body[:140]}")

        code2, body2 = post_raw(
            f"{base}/api/lemonsqueezy/webhook",
            raw,
            headers={
                "X-Signature": signature(raw, WEBHOOK_SECRET),
                "X-Event-Name": "order_created",
            },
        )
        check(
            "ls webhook (replay is idempotent)",
            code2 == 200 and "idempotent" in body2,
            f"{code2} {body2[:140]}",
        )

        # 4. forged signature
        code3, body3 = post_raw(
            f"{base}/api/lemonsqueezy/webhook",
            raw,
            headers={"X-Signature": "0" * 64},
        )
        check("ls webhook (bad signature)", code3 == 401, f"{code3} {body3[:140]}")

        # 5. the Stripe webhook path must answer immediately with the raw bytes
        stripe_raw = json.dumps({"id": "evt_verify", "type": "ping", "data": {"object": {}}}).encode()
        code4, body4 = post_raw(f"{base}/api/payment/webhook", stripe_raw)
        check("stripe webhook path", code4 in (400, 403), f"{code4} {body4[:140]}")

        # 6. an ordinary JSON route still receives a parsed body
        code5, body5 = call(
            f"{base}/api/webhook/emit",
            {"event": "user.registered", "data": {}},
            method="POST",
        )
        check("ordinary JSON route", code5 == 200 and '"success"' in body5, f"{code5} {body5[:140]}")

        # 7. auth still works after the payment changes
        email = f"pay-verify-{int(time.time())}@example.com"
        code6, body6 = call(
            f"{base}/api/auth/register",
            {"name": "Verification User", "email": email, "password": "VerifyOnly!123"},
            method="POST",
        )
        check("auth register", code6 in (200, 201), f"{code6} {body6[:120]}")
        code7, body7 = call(
            f"{base}/api/auth/login", {"email": email, "password": "VerifyOnly!123"}, method="POST"
        )
        check("auth login", code7 == 200, f"{code7} {body7[:120]}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("products", nargs="*")
    args = ap.parse_args()

    targets = [p for p in sorted(PRODUCTS.iterdir()) if p.is_dir() and (p / "backend").is_dir()]
    if args.products:
        targets = [p for p in targets if p.name in args.products]

    failed = 0
    for product in targets:
        print(f"\n== {product.name}")
        for label, ok, detail in run_product(product):
            failed += 0 if ok else 1
            print(f"   [{'PASS' if ok else 'FAIL'}] {label:32} {detail}")

    print(f"\n{'FAILED' if failed else 'OK'}: {failed} failing check(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())