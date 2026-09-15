# JARVIS home cluster

Flux YAML. Gitea is origin. This GitHub repo is a mirror. Do not point Flux at GitHub.

Canonical pins: ~/jarvis-infra/VERSION

| Item | Value |
| --- | --- |
| Pins | ~/jarvis-infra/VERSION |
| Flux origin | http://git.lan/jarvis/cluster.git |

## GitOps path

```mermaid
flowchart LR
  classDef src fill:#d1fae5,stroke:#047857,color:#111827
  classDef ctrl fill:#e0e7ff,stroke:#3730a3,color:#111827
  classDef mir fill:#f3f4f6,stroke:#6b7280,color:#111827
  Dev["agent on bastion"] -->|"git push"| Gitea["Gitea git.lan"]
  Gitea -->|"Flux reconcile"| Ctrl["ctrl-01"]
  Ctrl --> Workers["apps-01, gpu-01, gpu-02, data nodes"]
  Gitea -->|"mirror script"| GH["GitHub mirror"]
  class Gitea src
  class Ctrl ctrl
  class GH mir
```

## Workloads by node

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
    claw["OpenClaw :18789"]
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

Live Flux path: clusters/jarvis/apps/homepage.yaml
imagePullPolicy Never. SA homepage. Image from infra VERSION.

| Tag | What |
| --- | --- |
| v0.4.8 | event stream |
| v0.4.9 | colored README diagrams |
| v0.4.10 | VERSION contract |
