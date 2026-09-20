#!/usr/bin/env python3
"""OpenClaw OpenAI shim + constrained product verbs (D-0010 / D-0022)."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import subprocess
import traceback
import uuid

# Word forms for small node counts (TTS-friendly).

PORT = int(os.environ.get("SHIM_PORT", "4001"))
TIMEOUT = int(os.environ.get("OPENCLAW_ASK_TIMEOUT", "300"))
VERB_TIMEOUT = int(os.environ.get("VERB_TIMEOUT", "30"))

HEALTH = "/home/node/.openclaw/skills/cluster-health/k8s.js"
METRICS = "/home/node/.openclaw/skills/cluster-metrics/prom.js"
SKILL_DIRS = (
    "/home/node/.openclaw/skills/cluster-health",
    "/home/node/.openclaw/skills/cluster-metrics",
    "/home/node/.openclaw/skills/lab-map",
)

TRUSTED_VERBS = ("cluster.health", "cluster.gpus", "lab.map")
CONFIRM_VERBS = ("apps.recycle_pod", "apps.restart_deploy")
VERBS = TRUSTED_VERBS + CONFIRM_VERBS
WRITE_NS = frozenset({"apps", "inference", "agents", "monitoring"})
NAME_RE = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")

SURFACES = [
    {"name": "Product glass", "url": "https://jarvis.lan", "for": "Daily talk, voice, memory"},
    {"name": "NOC", "url": "https://noc.lan", "for": "Nodes, workloads, alerts"},
    {"name": "Chat (break-glass)", "url": "https://chat.lan", "for": "OWUI when glass is down"},
    {"name": "Agent (break-glass)", "url": "http://agent.lan:18789", "for": "OpenClaw UI"},
    {"name": "Grafana", "url": "https://grafana.lan", "for": "Graphs"},
    {"name": "Git (Flux origin)", "url": "http://git.lan", "for": "cluster YAML"},
    {"name": "LLM API", "url": "https://llm.lan/v1", "for": "OpenAI-shaped"},
]


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


def extract_text(raw):
    try:
        d = json.loads(raw)
    except Exception:
        return (raw or "").strip()[:8000]
    res = d.get("result") or d
    texts = [
        p.get("text")
        for p in (res.get("payloads") or [])
        if isinstance(p, dict) and p.get("text")
    ]
    vis = (res.get("meta") or {}).get("finalAssistantVisibleText")
    if vis:
        return str(vis)
    if texts:
        return texts[-1]
    if d.get("status") and d.get("status") != "ok":
        return "Hands: " + str(d.get("summary") or d.get("status"))
    return (raw or "").strip()[:4000]


def run_agent(msg):
    msg = (msg or "ping")[:8000]
    sid = "agent:main:" + uuid.uuid4().hex[:12]
    try:
        p = subprocess.run(
            [
                "openclaw",
                "agent",
                "--session-key",
                sid,
                "--message",
                msg,
                "--timeout",
                str(TIMEOUT),
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=TIMEOUT + 30,
        )
    except subprocess.TimeoutExpired:
        return (
            "Hands timed out waiting for OpenClaw. "
            "The action may still have completed; check the cluster."
        )
    raw = (p.stdout or "").strip()
    if not raw:
        err = (p.stderr or "").strip()[-1500:]
        return "Hands empty reply" + ((": " + err) if err else "")
    return extract_text(raw)


def run_cmd(argv):
    try:
        p = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=VERB_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    if p.returncode != 0:
        return None, (err or out or f"exit {p.returncode}")[:500]
    return out, None


def parse_nodes(raw: str) -> list[dict]:
    nodes = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line or line.startswith("count="):
            continue
        # name\tReady=True\tip
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        name = parts[0]
        ready = "True" in parts[1] if len(parts) > 1 else False
        ip = parts[2] if len(parts) > 2 else ""
        nodes.append({"name": name, "ready": ready, "ip": ip})
    return nodes


def parse_prom(raw: str, value_key: str) -> dict[str, float]:
    """Map instance=node -> numeric value from prom.js one-line samples."""
    out: dict[str, float] = {}
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.search(r'instance=([^,\s}]+)', line)
        vm = re.search(r"\}\s+([0-9.eE+-]+)\s*$", line) or re.search(
            r"\s([0-9.eE+-]+)\s*$", line
        )
        if not m or not vm:
            continue
        try:
            out[m.group(1)] = float(vm.group(1))
        except ValueError:
            continue
    return out


def fmt_bytes(n: float) -> str:
    for unit, div in (("GiB", 1024**3), ("MiB", 1024**2), ("KiB", 1024)):
        if n >= div:
            return f"{n / div:.1f} {unit}"
    return f"{int(n)} B"


def verb_cluster_health() -> dict:
    nodes_raw, err_n = run_cmd(["node", HEALTH, "nodes"])
    pods_raw, err_p = run_cmd(["node", HEALTH, "pods"])
    if err_n and not nodes_raw:
        return {"ok": False, "verb": "cluster.health", "error": err_n}
    nodes = parse_nodes(nodes_raw or "")
    ready = sum(1 for n in nodes if n.get("ready"))
    total = len(nodes)
    pod_summary = (pods_raw or "").strip() or (err_p or "pods unavailable")
    healthy = ready == total and total > 0
    words = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight"}
    if ready == total and total > 0:
        label = words.get(total, str(total))
        text = f"{label} nodes Ready."
    else:
        bad = [n["name"] for n in nodes if not n.get("ready")]
        text = f"{ready}/{total} nodes Ready"
        if bad:
            text += f" (not Ready: {', '.join(bad)})"
        text += "."
    # Prefer calm prose over raw helper dump.
    low = pod_summary.lower()
    if "all pods" in low and "(" in pod_summary:
        m = re.search(r"\((\d+)\s+total\)", pod_summary, re.I)
        n = m.group(1) if m else None
        if n and "running" in low:
            text += f" All {n} pods Running or Succeeded."
        else:
            text += " " + pod_summary[0].upper() + pod_summary[1:] + "."
    elif pod_summary:
        text += " " + pod_summary + "."
    return {
        "ok": True,
        "verb": "cluster.health",
        "class": "trusted",
        "text": text.strip(),
        "data": {
            "nodes": nodes,
            "ready_count": ready,
            "node_count": total,
            "pod_summary": pod_summary,
            "healthy": healthy,
        },
    }


def verb_cluster_gpus() -> dict:
    temp_raw, err_t = run_cmd(["node", METRICS, "nvidia_smi_temperature_gpu"])
    mem_raw, err_m = run_cmd(["node", METRICS, "nvidia_smi_memory_used_bytes"])
    if err_t and not temp_raw:
        return {"ok": False, "verb": "cluster.gpus", "error": err_t}
    temps = parse_prom(temp_raw or "", "temp")
    mems = parse_prom(mem_raw or "", "mem")
    nodes = sorted(set(temps) | set(mems))
    gpus = []
    bits = []
    for node in nodes:
        t = temps.get(node)
        m = mems.get(node)
        entry = {"node": node}
        if t is not None:
            entry["temp_c"] = t
        if m is not None:
            entry["mem_used_bytes"] = m
        gpus.append(entry)
        part = node
        if t is not None:
            part += f" {int(t)}°C"
        if m is not None:
            part += f", {fmt_bytes(m)} used"
        bits.append(part)
    if not bits:
        return {
            "ok": False,
            "verb": "cluster.gpus",
            "error": err_m or err_t or "no GPU samples",
        }
    text = "GPU status: " + "; ".join(bits) + "."
    return {
        "ok": True,
        "verb": "cluster.gpus",
        "class": "trusted",
        "text": text,
        "data": {"gpus": gpus},
    }


def verb_lab_map() -> dict:
    nodes_raw, _err = run_cmd(["node", HEALTH, "nodes"])
    nodes = parse_nodes(nodes_raw or "")
    lines = ["Lab surfaces:"]
    for s in SURFACES:
        lines.append(f"- {s['name']}: {s['url']} ({s['for']})")
    if nodes:
        ready = sum(1 for n in nodes if n.get("ready"))
        lines.append(f"Nodes: {ready}/{len(nodes)} Ready ({', '.join(n['name'] for n in nodes)}).")
    text = "\n".join(lines)
    return {
        "ok": True,
        "verb": "lab.map",
        "class": "trusted",
        "text": text,
        "data": {"surfaces": SURFACES, "nodes": nodes},
    }


def _validate_target(args: dict) -> tuple[str, str] | dict:
    ns = str((args or {}).get("namespace") or "").strip()
    name = str((args or {}).get("name") or "").strip()
    if ns not in WRITE_NS:
        return {"ok": False, "error": f"namespace not allowed: {ns or '(empty)'}"}
    if not NAME_RE.match(name):
        return {"ok": False, "error": f"bad name: {name or '(empty)'}"}
    return ns, name


def resolve_pod_name(ns: str, name: str) -> tuple[str | None, str | None]:
    """If name is a deploy/app prefix, resolve to a Running pod name."""
    # Replica-set style pod names usually have a 5+ char hash segment.
    parts = name.split("-")
    if len(parts) >= 3 and len(parts[-1]) >= 5:
        return name, None
    out, err = run_cmd(["node", HEALTH, "find-pod", ns, name])
    if err or not out:
        return None, err or "pod not found"
    return out.strip().splitlines()[0].strip(), None


def verb_recycle_pod(args: dict, confirmed: bool) -> dict:
    target = _validate_target(args)
    if isinstance(target, dict):
        return target
    ns, name = target
    resolved, err = resolve_pod_name(ns, name)
    if not resolved:
        return {"ok": False, "verb": "apps.recycle_pod", "error": err or "pod not found"}
    preview = {
        "namespace": ns,
        "name": resolved,
        "requested": name,
        "summary": f"recycle pod {ns}/{resolved}",
    }
    if not confirmed:
        return {
            "ok": False,
            "verb": "apps.recycle_pod",
            "class": "confirm",
            "error": "confirm required",
            "preview": preview,
            "text": f"Confirm: recycle pod `{ns}/{resolved}`? Say yes or cancel.",
        }
    out, err = run_cmd(["node", HEALTH, "delete-pod", ns, resolved])
    if err:
        return {"ok": False, "verb": "apps.recycle_pod", "error": err}
    text = (out or f"Deleted pod {ns}/{resolved}.").strip()
    return {
        "ok": True,
        "verb": "apps.recycle_pod",
        "class": "confirm",
        "text": text if text.endswith(".") else text + ".",
        "data": {"namespace": ns, "name": resolved, "action": "deleted"},
    }


def verb_restart_deploy(args: dict, confirmed: bool) -> dict:
    target = _validate_target(args)
    if isinstance(target, dict):
        return target
    ns, name = target
    preview = {
        "namespace": ns,
        "name": name,
        "summary": f"restart deployment {ns}/{name}",
    }
    if not confirmed:
        return {
            "ok": False,
            "verb": "apps.restart_deploy",
            "class": "confirm",
            "error": "confirm required",
            "preview": preview,
            "text": f"Confirm: restart deployment `{ns}/{name}`? Say yes or cancel.",
        }
    out, err = run_cmd(["node", HEALTH, "restart-deploy", ns, name])
    if err:
        return {"ok": False, "verb": "apps.restart_deploy", "error": err}
    text = (out or f"Restarted deployment {ns}/{name}.").strip()
    return {
        "ok": True,
        "verb": "apps.restart_deploy",
        "class": "confirm",
        "text": text if text.endswith(".") else text + ".",
        "data": {"namespace": ns, "name": name, "action": "restarted"},
    }


def run_verb(verb: str, args: dict | None = None, confirmed: bool = False) -> dict:
    verb = (verb or "").strip()
    args = args or {}
    if verb == "cluster.health":
        return verb_cluster_health()
    if verb == "cluster.gpus":
        return verb_cluster_gpus()
    if verb == "lab.map":
        return verb_lab_map()
    if verb == "apps.recycle_pod":
        return verb_recycle_pod(args, confirmed)
    if verb == "apps.restart_deploy":
        return verb_restart_deploy(args, confirmed)
    return {"ok": False, "verb": verb, "error": "unknown verb"}


def deep_health() -> dict:
    skills = {}
    all_ok = True
    for d in SKILL_DIRS:
        name = d.rsplit("/", 1)[-1]
        present = os.path.isdir(d) and any(
            f.endswith(".js") or f == "SKILL.md" for f in (os.listdir(d) if os.path.isdir(d) else [])
        )
        skills[name] = present
        if not present:
            all_ok = False
    probe_ok = False
    probe_err = None
    if skills.get("cluster-health"):
        out, err = run_cmd(["node", HEALTH, "nodes"])
        if out and not err:
            probe_ok = True
        else:
            probe_err = err or "empty"
            all_ok = False
    else:
        all_ok = False
        probe_err = "skill missing"
    return {
        "ok": all_ok,
        "verbs": list(VERBS),
        "skills_mounted": skills,
        "nodes_probe": probe_ok,
        "nodes_probe_error": probe_err,
    }


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[shim]", fmt % args, flush=True)

    def _send(self, code, obj, ctype="application/json"):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/healthz", "/health", "/ready"):
            h = deep_health()
            self._send(200 if h.get("ok") else 503, h)
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            self._send(400, {"error": "bad json"})
            return
        path = self.path.split("?")[0]

        if path == "/v1/verbs":
            try:
                args = body.get("args") if isinstance(body.get("args"), dict) else {}
                confirmed = bool(body.get("confirmed"))
                result = run_verb(str(body.get("verb") or ""), args, confirmed)
            except Exception:
                print("[shim] verb error\n" + traceback.format_exc()[-1500:], flush=True)
                result = {"ok": False, "error": "verb failed"}
            # Propose (confirm required) is 200 so orch can read preview.
            if result.get("error") == "confirm required":
                self._send(200, result)
                return
            self._send(200 if result.get("ok") else 400, result)
            return

        if path not in ("/v1/chat/completions", "/chat/completions"):
            self._send(404, {"error": "not found"})
            return
        stream = bool(body.get("stream"))
        try:
            text = run_agent(last_user(body))
        except Exception:
            print("[shim] agent error\n" + traceback.format_exc()[-1500:], flush=True)
            text = "Hands error (see shim logs)."
        if stream:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            chunk = {
                "id": "chatcmpl-hands",
                "object": "chat.completion.chunk",
                "model": "jarvis-hands",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": text},
                        "finish_reason": None,
                    }
                ],
            }
            done = {
                "id": "chatcmpl-hands",
                "object": "chat.completion.chunk",
                "model": "jarvis-hands",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            self.wfile.write(b"data: " + json.dumps(chunk).encode() + b"\n\n")
            self.wfile.write(b"data: " + json.dumps(done).encode() + b"\n\n")
            self.wfile.write(b"data: [DONE]\n\n")
            return
        self._send(
            200,
            {
                "id": "chatcmpl-hands",
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
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
