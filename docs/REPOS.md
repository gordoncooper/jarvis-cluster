# JARVIS git layout

Living pins: **`~/jarvis-infra/VERSION`**. This file is layout, not the pin.

GitHub account: **https://github.com/gordoncooper** (private).
GitHub is **mirror only**. Flux origin stays `http://git.lan/jarvis/cluster.git`.
PHASE1-22 stay as history. Do not rewrite them when VERSION moves.

Two repos:

- `gordoncooper/jarvis-infra` — metal, Ansible, rebuild runbook, homepage image
- `gordoncooper/jarvis-cluster` — `git push --mirror` of Gitea (Flux YAML)

No third repo. No Flux -> GitHub.

SOPS + age lives in **jarvis-infra** (`secrets/secrets.sops.yaml`).
Rebuild: `materialize-bastion-secrets.sh` then `apply-secrets.sh`.
See jarvis-infra `docs/REBUILD.md` and `docs/OPERATING.md`.
