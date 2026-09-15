#!/bin/bash
# No kernel pin. Disables unattended-upgrades, dist-upgrades, installs NVIDIA
# modules for every kernel in /boot, reboots workers then ctrl-01.
#   ./cluster-update-reboot.sh              # dry-run
#   CONFIRM=yes ./cluster-update-reboot.sh  # do it
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
echo "----- kernels now -----"
for h in "${NODES[@]}"; do printf "%-8s " "$h"; ssh "$h" uname -r; done
if [ "$CONFIRM" != "yes" ]; then
  echo; echo "DRY-RUN. CONFIRM=yes will snapshot, disable auto-apt, dist-upgrade,"
  echo "install nvidia modules for upcoming kernels, reboot workers then ctrl-01."
  exit 0
fi
echo "----- 0. etcd snapshot -----"; ssh ctrl-01 'sudo k3s etcd-snapshot save' || true
echo "----- 1. disable automatic apt -----"
for h in "${NODES[@]}"; do
  echo "=== $h ==="
  ssh "$h" 'sudo bash -s' << 'REMOTE'
set -e
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
echo "----- 2. dist-upgrade -----"
for h in "${NODES[@]}"; do
  echo "=== apt $h ==="
  ssh "$h" 'sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::=--force-confold dist-upgrade'
done
echo "----- 3. NVIDIA modules for kernels that will boot -----"
for h in "${GPU_NODES[@]}"; do
  echo "=== nvidia $h ==="
  ssh "$h" 'sudo bash -s' << 'REMOTE'
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get install -y linux-headers-generic-hwe-26.04 \
  linux-modules-nvidia-595-server-open-generic-hwe-26.04 \
  nvidia-utils-595-server nvidia-compute-utils-595-server || true
for k in /boot/vmlinuz-*; do
  K=${k#/boot/vmlinuz-}
  echo "ABI $K"
  apt-get install -y "linux-headers-$K" || true
  apt-get install -y "linux-modules-nvidia-595-server-open-$K" || true
done
nvidia-smi -L || true
REMOTE
done
echo "----- 4. reboot workers -----"
for h in "${WORKERS[@]}"; do
  echo "rebooting $h"; ssh "$h" 'sudo reboot' || true; sleep 8; wait_ssh "$h"
done
echo "----- 5. reboot ctrl-01 last -----"
ssh ctrl-01 'sudo reboot' || true; sleep 15; wait_ssh ctrl-01
echo -n "waiting apiserver "
for i in $(seq 1 40); do
  kubectl get --raw=/readyz >/dev/null 2>&1 && { echo ok; break; }
  echo -n .; sleep 5
done
kubectl get nodes -o wide
echo "----- 6. GPU -----"
for n in gpu-01 gpu-02; do
  ssh "$n" 'echo -n "$(hostname) $(uname -r) "; nvidia-smi --query-gpu=name,driver_version,memory.used --format=csv,noheader'
  kubectl get node "$n" -o jsonpath='gpu={.status.allocatable.nvidia\.com/gpu}{"\n"}'
done
kubectl -n inference get pods -o wide
echo "----- 7. NFS -----"
for h in ctrl-01 gpu-01 gpu-02 data-02 apps-01; do
  ssh "$h" 'findmnt /mnt/nfs >/dev/null || sudo mount /mnt/nfs; findmnt -n /mnt/nfs | awk "{print \$1,\$2}"'
done
echo "======== DONE — run scripts/smoke-operator.sh ========"
