# cluster — how to work in this repo

Flux YAML only. Gitea is origin. GitHub is a mirror, and it can lag.

The operating contract for the house is jarvis-infra
[AGENTS.md](https://github.com/gordoncooper/jarvis-infra/blob/main/AGENTS.md).
Product calls are jarvis-infra
[docs/DECISIONS.md](https://github.com/gordoncooper/jarvis-infra/blob/main/docs/DECISIONS.md).
A dated decision outranks prose here.

## Rules

- Edit on the bastion as `agent`. Push to `http://git.lan/jarvis/cluster.git`.
- Keep `path: ./clusters/jarvis`. Do not rename it.
- Do not `kubectl apply -f`. Flux reconciles this repo.
- Never push this repo to GitHub as if it were origin.
- Read the live object (`kubectl get`) before changing its YAML.
- A workload that is running but has no YAML here is an orphan. Find it on the cluster and adopt it. Do not decide it does not exist because the tree is silent.
- Product images are built from `~/jarvis-app`. Their Deployments live under `clusters/jarvis/apps/`. Pin the tag here after the image is imported. `imagePullPolicy: Never`.
- `.claude/settings.json` is the deny-rule set, not a second contract. Keep it committed. `~/.agent-guard.sh` refuses a push that treats GitHub as origin.

## Laptop clone

A GitHub checkout on a laptop is a read-only cache. Do not push it as origin. Do not kubectl from it. Edit on the bastion.
