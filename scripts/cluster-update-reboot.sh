#!/bin/bash
# Manual cluster update + reboot. Does NOT pin kernels.
set -euo pipefail
NODES=(ctrl-01 gpu-01 gpu-02 data-01 data-02 apps-01)
WORKERS=(gpu-01 gpu-02 apps-01 data-02 data-01)
GPU_NODES=(gpu-01 gpu-02)
CONFIRM="${CONFIRM:-no}"
ssh_ok() { ssh -o ConnectTimeout=8 -o BatchMode=yes "$1" true 2>/dev/null; }
wait_ssh() {
  local h=$1 n=0
  echo -n "waiting ssh $h "
  while ! ssh_ok "$h"; do
    n=$((n+1)); [ "$n" -gt 60 ] && { echo TIMEOUT; return 1; }
    echo -n .; sleep 5
  done; echo ok
}
echo "======== JARVIS UPDATE+REBOOT $(date -Is) CONFIRM=$CONFIRM ========"
for h in "${NODES[@]}"; do printf "%-8s " "$h"; ssh "$h" uname -r; done
if [ "$CONFIRM" != "yes" ]; then
  echo "DRY-RUN. CONFIRM=yes → snapshot, auto-apt off, dist-upgrade, HWE nvidia only, reboot, drop Unknown, wait home.lan."
  exit 0
fi
ssh ctrl-01 'sudo k3s etcd-snapshot save --config /etc/rancher/k3s/snapshot.yaml' || true
for h in "${NODES[@]}"; do
  echo "=== disable apt $h ==="
  ssh "$h" 'sudo bash -s' << 'REMOTE'
systemctl disable --now unattended-upgrades.service 2>/dev/null || true
systemctl disable --now apt-daily.timer apt-daily-upgrade.timer 2>/dev/null || true
systemctl mask unattended-upgrades.service apt-daily.service apt-daily-upgrade.service 2>/dev/null || true
cat > /etc/apt/apt.conf.d/20auto-upgrades << 'C'
APT::Periodic::Update-Package-Lists "0";
APT::Periodic::Unattended-Upgrade "0";
APT::Periodic::Download-Upgradeable-Packages "0";
APT::Periodic::AutocleanInterval "0";
C
REMOTE
done
for h in "${NODES[@]}"; do
  echo "=== apt $h ==="
  ssh "$h" 'sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::=--force-confold dist-upgrade'
done
for h in "${GPU_NODES[@]}"; do
  echo "=== nvidia HWE only $h ==="
  ssh "$h" 'sudo bash -s' << 'REMOTE'
export DEBIAN_FRONTEND=noninteractive
apt-get install -y linux-headers-generic-hwe-26.04 \
  linux-modules-nvidia-595-server-open-generic-hwe-26.04 \
  nvidia-utils-595-server nvidia-compute-utils-595-server || true
nvidia-smi -L || echo "(NVML mismatch before reboot is expected)"
REMOTE
done
for h in "${WORKERS[@]}"; do echo "rebooting $h"; ssh "$h" 'sudo reboot' || true; sleep 8; wait_ssh "$h"; done
ssh ctrl-01 'sudo reboot' || true; sleep 15; wait_ssh ctrl-01
echo -n "waiting apiserver "
for i in $(seq 1 40); do kubectl get --raw=/readyz >/dev/null 2>&1 && { echo ok; break; }; echo -n .; sleep 5; done
kubectl wait --for=condition=Ready node --all --timeout=180s || true
for n in gpu-01 gpu-02; do
  ssh "$n" 'echo -n "$(hostname) $(uname -r) "; nvidia-smi --query-gpu=name,driver_version,memory.used --format=csv,noheader'
  kubectl get node "$n" -o jsonpath='gpu={.status.allocatable.nvidia\.com/gpu}{"\n"}'
done
kubectl get pods -A --field-selector=status.phase==Unknown -o name 2>/dev/null | while read -r p; do
  kubectl delete "$p" --force --grace-period=0 2>/dev/null || true
done
kubectl wait --for=condition=available -n inference deploy/ollama deploy/ollama-embed --timeout=180s || true
kubectl wait --for=condition=available -n apps deploy/open-webui deploy/homepage --timeout=180s || true
for h in ctrl-01 gpu-01 gpu-02 data-02 apps-01; do
  ssh "$h" 'findmnt /mnt/nfs >/dev/null || sudo mount /mnt/nfs; findmnt -n /mnt/nfs | awk "{print \$1,\$2}"'
done
for i in $(seq 1 24); do
  code=$(curl -skS -o /dev/null -w "%{http_code}" --max-time 5 https://home.lan/ || echo 000)
  [ "$code" = "200" ] && { echo "home.lan 200"; break; }
  echo "home.lan $code …"; sleep 5
done
echo "======== DONE — run scripts/smoke-operator.sh ========"
