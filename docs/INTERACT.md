# How to talk to JARVIS

- **https://home.lan** — command board. Header LIVE = Prometheus, SIM = fallback.
- **https://home.lan/status** — GPU temp/VRAM, node CPU/RAM, workloads.
- **https://chat.lan** — Open WebUI. jarvis-local (free) or jarvis-grok* (SuperGrok).
- **http://agent.lan:18789** — OpenClaw. DNS must be 192.168.8.16. HTTP on purpose.
- **goose session** on bastion — terminal agent; OPENAI_HOST=https://llm.lan
- **https://grafana.lan** — graphs, NVIDIA 14574.
- **https://llm.lan/v1** — LiteLLM, OpenAI-shaped.
- **http://git.lan** — Gitea, Flux origin, stays HTTP.
- **ssh bastion** — break-glass.

Pick jarvis-local for chatter and RAG. Pick jarvis-grok-code when it must run tools or write YAML.
