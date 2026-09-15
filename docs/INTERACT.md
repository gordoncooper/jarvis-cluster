# How to talk to JARVIS

Canonical copy: `jarvis-infra/docs/INTERACT.md`.

| Surface | URL / cmd | Best for | Model / cost |
| --- | --- | --- | --- |
| Command board | https://home.lan | Services + rack + compact events. Header **LIVE** = Prometheus. | — |
| Status floor | https://home.lan/status | GPU temp/VRAM, 10-min event stream, nodes | — |
| Telemetry | https://home.lan/api/telemetry | JSON snapshot | — |
| Chat | https://chat.lan | Q&A, RAG, voice | `jarvis-local` free; `jarvis-grok*` SuperGrok |
| Agent | http://agent.lan:18789 | Cluster ops | `jarvis-grok-code` (API) |
| Goose | `goose session` on bastion | Terminal agent | `jarvis-grok-code` via **https://llm.lan** |
| Grafana | https://grafana.lan | NVIDIA 14574 | — |
| API | https://llm.lan/v1 | OpenAI-shaped | LiteLLM |
| GitOps | http://git.lan | YAML in `~/cluster` as **agent** | — |

**git.lan stays HTTP**. **agent.lan:18789** is HTTP (hostPort). DNS **192.168.8.16**.
Pins: `~/jarvis-infra/VERSION`.
