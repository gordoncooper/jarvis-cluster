---
name: flux-pin
description: Pin JARVIS image tags or edit Flux YAML. Use when changing clusters/jarvis/apps, Deployments, image pins, or anything Flux reconciles. Not for metal or jarvis-app source.
---

# flux-pin

- Edit ~/cluster as agent. Push Gitea. GitHub jarvis-cluster is a cache. Never push this clone to GitHub as origin.
- path stays ./clusters/jarvis
- Read the live object (kubectl get) before editing YAML. Then edit YAML. Never kubectl apply. Flux reconciles. Documented exception remains apps/jarvis-noc/install-noc.sh only if that is the task.
- Do not touch flux-system/gotk-components.yaml or monitoring Grafana JSON unless that is the task.
- Product glass + orchestrator Deployments live under clusters/jarvis/apps/. Pin the tag from jarvis-app VERSION after ship-image. Do not invent a tag.
- One coherent change per commit.
- Laptop GitHub clone of this repo is read-only.
