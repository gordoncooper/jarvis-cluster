#!/bin/bash
set -u
KEY=$(cat "$HOME/.litellm-master.key" 2>/dev/null || true)
code() { curl -skS -o /dev/null -w "%{http_code}" --max-time 10 "$1" 2>/dev/null || echo ERR; }
echo "======== JARVIS OPERATOR SMOKE $(date -Is) ========"
kubectl get nodes -o wide
echo
kubectl get pods -A --field-selector=status.phase!=Succeeded | grep -v Running | grep -v Completed || echo "(all Running/Completed)"
echo; echo "----- HTTPS -----"
for u in "home https://home.lan/" "chat https://chat.lan/health" "grafana https://grafana.lan/" \
         "llm https://llm.lan/health/liveliness" "gitea http://git.lan/api/healthz" \
         "agent http://agent.lan:18789/"; do
  set -- $u; printf "%-8s %s  %s\n" "$1" "$2" "$(code "$2")"
done
echo "----- GPU -----"
for n in gpu-01 gpu-02; do
  echo -n "$n "; kubectl get node "$n" -o jsonpath='gpu={.status.allocatable.nvidia\.com/gpu}{"\n"}'
  ssh "$n" nvidia-smi --query-gpu=name,memory.used,temperature.gpu --format=csv,noheader
done
echo "----- jarvis-local -----"
curl -skS --max-time 90 https://llm.lan/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  -d '{"model":"jarvis-local","messages":[{"role":"user","content":"Reply with exactly: jarvis-ok"}],"max_tokens":16}' \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print((d.get("choices") or [{}])[0].get("message",{}).get("content") or d)'
echo "----- grok-code -----"
curl -skS --max-time 60 https://llm.lan/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  -d '{"model":"jarvis-grok-code","messages":[{"role":"user","content":"Reply with exactly: grok-ok"}],"max_tokens":16}' \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print((d.get("choices") or [{}])[0].get("message",{}).get("content") or d)'
echo "----- models / flux / backup -----"
kubectl -n inference exec deploy/ollama -- ollama list
kubectl -n inference exec deploy/ollama-embed -- ollama list
kubectl -n flux-system get kustomization flux-system
git -C ~/cluster describe --tags --always
ssh data-01 'sudo bash -c "ls -1dt /cluster/nfs/backups/*/ 2>/dev/null | head -2; ls /cluster/nfs/snapshots | tail -2"'
echo "======== CLI HALF DONE — browser steps: docs/SMOKE-OPERATOR.md ========"
