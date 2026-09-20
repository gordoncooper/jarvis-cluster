# JARVIS cluster YAML

Flux YAML only. **Gitea is origin.** GitHub is a mirror.

This repo has no bible. The contract is jarvis-infra
[AGENTS.md](https://github.com/gordoncooper/jarvis-infra/blob/main/AGENTS.md),
then [docs/DECISIONS.md](https://github.com/gordoncooper/jarvis-infra/blob/main/docs/DECISIONS.md).
A dated decision outranks any prose here or there.

Rules specific to this repo:

- Edit and `git push` from bastion `~/cluster` to `http://git.lan/jarvis/cluster.git`
- Keep `path: ./clusters/jarvis` — do not rename it
- Do not `kubectl apply -f` here; Flux reconciles this repo
- Never push this repo to GitHub as if it were origin
- Read the live object (`kubectl get`) before changing its YAML
- `.claude/settings.json` is deny-rules for Claude Code and Grok CLI, not a
  second bible (D-0007). Keep it committed. Gitea-origin is enforced by
  `~/.agent-guard.sh`.

Not everything on the cluster is in this repo. `jarvis.lan` and `noc.lan` are
applied outside Flux from `jarvis-core/deploy/scripts/`. If you cannot find a
workload's YAML here, that is why — check the live cluster before concluding it
does not exist.

If this workspace is a **laptop GitHub clone**: it is a read-only cache. Do not
push it as origin, and do not kubectl from a laptop. Edit on the bastion.
Prefer Cursor Remote-SSH as user `agent`.
