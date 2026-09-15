# JARVIS home cluster

Six ThinkCentre M920x + bastion. k3s, Flux, Gitea.
**Gitea is origin. GitHub is mirror only.** Metal: https://github.com/gordoncooper/jarvis-infra

Known-good tag: **v0.4.4** (`jarvis-home:v0.2`). This tree: **jarvis-home:v0.4.5** (Prometheus tiles).

| Phase | Doc | Status |
|---|---|---|
| 21 Command center | PHASE21.md | https://home.lan + /status |
| 22 Prometheus tiles | PHASE22.md | jarvis-home:v0.4.5 scrape |

| URL | App |
|---|---|
| https://home.lan | Command center |
| https://chat.lan | Open WebUI |
| http://agent.lan:18789 | OpenClaw |
| https://llm.lan/v1 | LiteLLM |
| http://git.lan | Gitea |
| https://grafana.lan | Grafana |
