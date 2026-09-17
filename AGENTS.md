# JARVIS cluster YAML

Flux YAML only. **Gitea is origin.** GitHub is a mirror.

Copilot index is **jarvis-infra** [docs/COPILOT.md](https://github.com/gordoncooper/jarvis-infra/blob/main/docs/COPILOT.md)
and [AGENTS.md](https://github.com/gordoncooper/jarvis-infra/blob/main/AGENTS.md). This repo has no second bible.

- Edit and `git push` from bastion `~/cluster` to `http://git.lan/jarvis/cluster.git`
- Never `git push` this repo to GitHub from a laptop as if it were origin
- Never put kubeconfig on a laptop
- Session 0 discover on the bastion before any YAML change
- Do not `kubectl apply -f` (bypasses Flux)
