# JARVIS cluster (Flux YAML)

Maturity is infra `VERSION` `MATURITY` (not copied here). License: [MIT](LICENSE).

Flux YAML for the six-node k3s lab. **Gitea is origin.** This GitHub
repository is a **mirror**. Do not point Flux at GitHub.

Metal, Ansible, scripts, and the homepage **image** live in
[gordoncooper/jarvis-infra](https://github.com/gordoncooper/jarvis-infra).

This file is the map of **what Flux applies**. Operator contract, discover,
and rebuild live in infra (`AGENTS.md`, `docs/COPILOT.md`, `docs/OPERATING.md`).
This repo's [AGENTS.md](AGENTS.md) is a stub — no second bible.

If you opened a **laptop GitHub clone**: it is a cache. Do not `git push`
this remote as origin. Do not kubectl from a laptop. Edit `~/cluster` on
the bastion as user **agent** and push to Gitea.

Canonical pins: `~/jarvis-infra/VERSION` on the bastion. Do not copy
git/image tags into this file.

| | |
| --- | --- |
| Flux origin | `http://git.lan/jarvis/cluster.git` |
| Path Flux reads | `./clusters/jarvis` (do not rename) |
| k3s | single-server etcd on ctrl-01 (`K3S` in infra VERSION) |
| Glass | **jarvis.lan** is the product; **noc.lan** is the operator surface (D-0002). chat.lan and agent.lan are break-glass. |

`noc.lan` is served by `jarvis-noc`, reconciled from this repo since D-0038.
Its **image** is built out of band by `jarvis-infra apps/jarvis-noc/install-noc.sh`,
because `imagePullPolicy: Never` means Flux cannot pull it — build first, then
reconcile. `home.lan` (`apps/homepage.yaml`) is legacy and retiring into
noc.lan; it still serves.

## Use cases

- **Local chat** — Open WebUI → LiteLLM → Ollama 7B Q6 on gpu-01.
- **Grok on demand** — same OpenAI-shaped API, `jarvis-grok` / `jarvis-grok-code`.
- **RAG** — embeddings on gpu-02, knowledge in Open WebUI (`lab-docs`, `jarvis-learned`).
- **Voice** — Whisper STT on chat.lan; Piper TTS on apps-01.
- **Hands** — in-glass `jarvis-hands` (OpenClaw shim in the OpenClaw pod).
- **See the rack** — https://noc.lan (https://home.lan is legacy) and https://grafana.lan.
- **GitOps** — edit YAML as `agent`, push Gitea, Flux reconciles.

Do not add exact-phrase `keyword_tier_rules`. Prefer vendor knobs
(LiteLLM config, OpenClaw skills, k8s RBAC).

## GitOps path

```mermaid
sequenceDiagram
  actor Dev as agent on bastion
  participant Gitea as Gitea git.lan
  participant Flux as Flux on ctrl-01
  participant Nodes as apps / gpu / data
  participant GH as GitHub mirror
  Dev->>Gitea: git push main
  Gitea->>Flux: GitRepository reconcile
  Flux->>Nodes: apply clusters/jarvis
  Dev->>Gitea: mirror-to-github.sh
  Gitea->>GH: git push --mirror
```


```mermaid
flowchart LR
  classDef src fill:#d1fae5,stroke:#047857,color:#111827
  classDef ctrl fill:#e0e7ff,stroke:#3730a3,color:#111827
  classDef mir fill:#f3f4f6,stroke:#6b7280,color:#111827
  Dev["agent ~/cluster"] -->|"git push"| Gitea["Gitea git.lan"]
  Gitea -->|"reconcile"| Ctrl["Flux on ctrl-01"]
  Ctrl --> Workers["apps-01 gpu-01 gpu-02 data-*"]
  Gitea -->|"mirror"| GH["GitHub cache"]
  class Gitea src
  class Ctrl ctrl
  class GH mir
```


## Tree

```mermaid
flowchart TB
  classDef root fill:#e0e7ff,stroke:#3730a3,color:#111827
  FS["clusters/jarvis/kustomization.yaml"]
  FS --> Inf["inference/"]
  FS --> Apps["apps/"]
  FS --> Ag["agents/"]
  FS --> Mon["monitoring/"]
  FS --> Tls["tls/"]
  Inf --> Oll["ollama.yaml  ollama-embed.yaml"]
  Inf --> Lit["litellm.yaml  litellm-config.yaml"]
  Inf --> DP["device-plugin.yaml"]
  Apps --> OW["open-webui.yaml"]
  Apps --> Hud["jarvis-webui-hud.yaml"]
  Apps --> Home["homepage.yaml"]
  Apps --> Pip["piper.yaml"]
  Ag --> OC["openclaw.yaml  rbac.yaml"]
  Ag --> Sk["skill ConfigMaps"]
  Mon --> Pr["prometheus grafana exporters"]
  Tls --> TS["TLSStore mkcert"]
  class FS root
```


Keep `path: ./clusters/jarvis`. Gitea is the Flux GitRepository URL.

## Namespaces and placement

Bastion (192.168.8.10) is omitted — not a k3s node.

```mermaid
flowchart TB
  classDef ctrl fill:#e0e7ff,stroke:#3730a3,color:#111827
  classDef gpu fill:#d1fae5,stroke:#047857,color:#111827
  classDef store fill:#fef3c7,stroke:#b45309,color:#111827
  classDef apps fill:#fce7f3,stroke:#9d174d,color:#111827

  subgraph nctrl["ctrl-01  192.168.8.11"]
    k3s["k3s server + etcd"]
    giteaN["Gitea"]
    flux["Flux"]
    traefik["Traefik / TLSStore"]
  end
  subgraph ngpu1["gpu-01  192.168.8.12"]
    ollama["Ollama jarvis-local"]
    gex1["nvidia-gpu-exporter"]
  end
  subgraph ngpu2["gpu-02  192.168.8.13"]
    embed["Ollama nomic-embed"]
    gex2["nvidia-gpu-exporter"]
  end
  subgraph ndata1["data-01  192.168.8.14"]
    nfs["NFS /cluster"]
  end
  subgraph ndata2["data-02  192.168.8.15"]
    prom["Prometheus"]
    graf["Grafana"]
    ksm["kube-state-metrics"]
  end
  subgraph napps["apps-01  192.168.8.16"]
    webui["Open WebUI"]
    litellm["LiteLLM"]
    piper["Piper"]
    claw["OpenClaw :18789 + shim :4001"]
    home["jarvis-home :3000"]
  end
  webui --> litellm
  claw --> litellm
  litellm --> ollama
  litellm --> embed
  home --> prom
  graf --> prom

  class nctrl,k3s,giteaN,flux,traefik ctrl
  class ngpu1,ngpu2,ollama,embed,gex1,gex2 gpu
  class ndata1,ndata2,nfs,prom,graf,ksm store
  class napps,webui,litellm,piper,claw,home apps
```


| Path | Namespace | What |
| --- | --- | --- |
| jarvis-infra `bootstrap/gitea.yaml` (not Flux) | gitea | git.lan |
| `clusters/jarvis/inference/` | inference | Ollama, embed, LiteLLM, RuntimeClass, device plugin |
| `clusters/jarvis/apps/` | apps | Open WebUI, Piper, homepage, HUD ConfigMap |
| `clusters/jarvis/agents/` | agents | OpenClaw, shim, skills, RBAC |
| `clusters/jarvis/monitoring/` | monitoring | Prometheus, Grafana, exporters |
| `clusters/jarvis/tls/` | traefik | mkcert TLSStore |

Node labels: `jarvis.role=control|gpu|storage|apps`.

## Ingress

```mermaid
flowchart LR
  classDef vip fill:#e0e7ff,stroke:#3730a3,color:#111827
  classDef host fill:#fce7f3,stroke:#9d174d,color:#111827
  DNS["router DNS"] --> T["Traefik  ctrl-01 .11"]
  DNS --> HP["hostPort  apps-01 .16"]
  T --> jarvis["jarvis.lan :443 (not Flux)"]
  T --> noc["noc.lan :443 (not Flux)"]
  T --> home["home.lan :443 legacy"]
  T --> chat["chat.lan :443"]
  T --> llm["llm.lan :443"]
  T --> graf["grafana.lan :443"]
  T --> git["git.lan :80 HTTP"]
  HP --> agent["agent.lan:18789 HTTP"]
  class T vip
  class HP,agent host
```


`agent.lan` must resolve to **192.168.8.16**. Traefik on ctrl-01 cannot
hold that hostPort. `git.lan` stays HTTP on purpose (Flux origin).

## Router (chat.lan)

```mermaid
sequenceDiagram
  actor You
  participant W as Open WebUI chat.lan
  participant L as LiteLLM apps-01
  participant Q as Ollama gpu-01
  participant C as OpenClaw shim :4001
  participant X as xAI
  You->>W: prompt to alias jarvis
  W->>L: /v1/chat/completions
  alt talk / RAG
    L->>Q: ollama/jarvis
  else inspect / recycle
    L->>C: model jarvis-hands
  else YAML / hard
    L->>X: grok-code / grok
  end
```


Default alias is `jarvis` (LiteLLM `complexity_router`).
Picker stays as Tony's hatch. Prefixes `local:` `hands:` `code:` `grok:`
are an Open WebUI filter — do not grow that pet. Do not add keyword rules.

Ollama, Piper, LiteLLM, monitoring images are **digest-pinned**
(`:tag@sha256:…`, `IfNotPresent`). Homepage is **not** pulled — see below.

## OpenClaw (Hands)

```mermaid
flowchart LR
  classDef pod fill:#fce7f3,stroke:#9d174d,color:#111827
  classDef rbac fill:#e0e7ff,stroke:#3730a3,color:#111827
  L["LiteLLM jarvis-hands"] --> Shim["openai-shim :4001"]
  Shim --> Gw["gateway :18789"]
  Gw --> Skills["skills ConfigMaps"]
  Gw --> SA["SA openclaw"]
  SA --> Recycle["Role openclaw-recycle"]
  Recycle --> NS["apps inference agents monitoring"]
  class Shim,Gw,Skills pod
  class SA,Recycle,NS rbac
```


In-glass only for normal use. http://agent.lan:18789 and
`jarvis-infra/scripts/openclaw-ask.sh` are break-glass.
Writes in git today: recycle (pod delete + deploy patch). Not cluster-admin.
**Cat live RBAC before widening.** Recycle the pod → re-pair the Control UI.

## Homepage contract

Image is built on apps-01 from jarvis-infra (`install-jarvis-home.sh` reads
`VERSION`) **before** Flux applies `homepage.yaml`. `imagePullPolicy: Never`.
SA `homepage` lists events, pods, nodes, Flux CRs.

Keep `clusters/jarvis/apps/homepage.yaml` in lockstep with
`jarvis-infra/apps/jarvis-home/homepage.yaml`.
`check-contract.sh` compares both.

HUD chrome for chat.lan is `clusters/jarvis/apps/jarvis-webui-hud.yaml`
(ConfigMap inject). Chrome is not routing.

## Data plane

```mermaid
flowchart TB
  classDef nfs fill:#fef3c7,stroke:#b45309,color:#111827
  classDef hp fill:#fce7f3,stroke:#9d174d,color:#111827
  NFS["data-01 /cluster/nfs"] --> B["backups/ stamps"]
  NFS --> Snap["snapshots/ etcd"]
  NFS --> LearnN["jarvis/learned.md mirror"]
  HP["apps-01 /cluster/local"] --> W["open-webui/"]
  HP --> O["openclaw/ learned.md MEMORY"]
  HP --> P["piper/ voices"]
  class NFS,B,Snap,LearnN nfs
  class HP,W,O,P hp
```


hostPath is the live app data. NFS is backup + learned mirror.
Do not commit `learned.md`.

## Change YAML

Work on the bastion clone of **Gitea**, not GitHub.

1. `cd ~/cluster` as user **agent**
2. Edit `clusters/jarvis/...` (keep `path: ./clusters/jarvis`)
3. `git push origin main` → `http://git.lan/jarvis/cluster.git`
4. Flux applies in about a minute, or:

       flux reconcile kustomization flux-system --with-source

5. Proof lives in infra: `~/jarvis-infra/scripts/verify-jarvis.sh`
6. Mirror (or wait for 03:30): `~/jarvis-infra/scripts/mirror-to-github.sh`

Example — digest pin lives on the container `image:` field as
`tag@sha256:…` plus `imagePullPolicy: IfNotPresent`. Homepage stays `Never`.

## Docs and scripts (infra)

Scripts (`check-contract.sh`, `verify-jarvis.sh`, backup, discover) live in
`~/jarvis-infra/scripts/`. This repo is YAML only.

- [COPILOT](https://github.com/gordoncooper/jarvis-infra/blob/main/docs/COPILOT.md)
- [OPERATING](https://github.com/gordoncooper/jarvis-infra/blob/main/docs/OPERATING.md)
- [INTERACT](https://github.com/gordoncooper/jarvis-infra/blob/main/docs/INTERACT.md)
- [REBUILD](https://github.com/gordoncooper/jarvis-infra/blob/main/docs/REBUILD.md)
- [RESTORE](https://github.com/gordoncooper/jarvis-infra/blob/main/docs/RESTORE.md)
- [LESSONS](https://github.com/gordoncooper/jarvis-infra/blob/main/docs/LESSONS.md)
- [PLAN](https://github.com/gordoncooper/jarvis-infra/blob/main/docs/PLAN.md)
