#!/usr/bin/env python3
"""OpenAI-compatible shim → `openclaw agent` (same pod netNS, gateway :18789)."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, os, subprocess, traceback

PORT = int(os.environ.get("SHIM_PORT", "4001"))
TIMEOUT = int(os.environ.get("OPENCLAW_ASK_TIMEOUT", "120"))


def last_user(body):
    for m in reversed(body.get("messages") or []):
        if m.get("role") != "user":
            continue
        c = m.get("content")
        if isinstance(c, list):
            return "".join(
                (x.get("text") or "") if isinstance(x, dict) else str(x) for x in c
            )
        return str(c or "")
    return ""


def run_agent(msg):
    msg = (msg or "ping")[:8000]
    p = subprocess.run(
        ["openclaw", "agent", "--message", msg, "--timeout", str(TIMEOUT), "--json"],
        capture_output=True,
        text=True,
        timeout=TIMEOUT + 20,
    )
    out = p.stdout or ""
    try:
        d = json.loads(out)
        texts = [
            x.get("text")
            for x in ((d.get("result") or {}).get("payloads") or [])
            if (x or {}).get("text")
        ]
        vis = ((d.get("result") or {}).get("meta") or {}).get(
            "finalAssistantVisibleText"
        )
        text = (texts[-1] if texts else vis) or out[:4000]
    except Exception:
        text = (out or p.stderr or "openclaw failed")[:4000]
    if p.returncode != 0 and not (p.stdout or "").strip():
        text = "openclaw exit %s: %s" % (p.returncode, (p.stderr or "")[:800])
    return text


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[shim]", args[0] if args else fmt)

    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path in ("/health", "/healthz"):
            return self._send(200, {"ok": True})
        if path in ("/v1/models", "/models"):
            return self._send(
                200,
                {"object": "list", "data": [{"id": "openclaw", "object": "model"}]},
            )
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            body = json.loads(raw or b"{}")
        except Exception:
            return self._send(400, {"error": "bad json"})
        if path not in ("/v1/chat/completions", "/chat/completions"):
            return self._send(404, {"error": "not found"})
        try:
            text = run_agent(last_user(body))
        except Exception:
            text = "shim error: " + traceback.format_exc()[-800:]
        return self._send(
            200,
            {
                "id": "chatcmpl-jarvis-hands",
                "object": "chat.completion",
                "model": "jarvis-hands",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }
                ],
            },
        )


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()
