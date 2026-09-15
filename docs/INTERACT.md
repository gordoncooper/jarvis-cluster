# How to talk to JARVIS

| Surface | URL / cmd | Best for |
|---|---|---|
| Command board | https://home.lan | Home. Header **LIVE** = Prometheus; **SIM** = fallback |
| Status floor | https://home.lan/status | GPU / node / workloads |
| Chat | https://chat.lan | `jarvis-local` or `jarvis-grok*` |
| Agent | http://agent.lan:18789 | OpenClaw |
| Grafana | https://grafana.lan | Graphs |
| GitOps | http://git.lan | YAML in `~/cluster` |

git.lan stays HTTP. agent.lan:18789 is HTTP on purpose.
