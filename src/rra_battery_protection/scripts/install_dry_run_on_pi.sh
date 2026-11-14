#!/usr/bin/env bash
set -euo pipefail

PKG_DIR="${1:-$HOME/rra_ws/src/rra_battery_protection}"
ROS_DISTRO="${ROS_DISTRO:-lyrical}"
WS="${RRA_WS:-$HOME/rra_ws}"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-205}"
export ROS_AUTOMATIC_DISCOVERY_RANGE="${ROS_AUTOMATIC_DISCOVERY_RANGE:-LOCALHOST}"

if [[ ! -f "$PKG_DIR/package.xml" ]]; then
  echo "No encuentro el paquete en $PKG_DIR" >&2
  exit 2
fi
if [[ ! -f "/opt/ros/$ROS_DISTRO/setup.bash" ]]; then
  echo "No existe /opt/ros/$ROS_DISTRO; confirma la distribución instalada" >&2
  exit 2
fi

source "/opt/ros/$ROS_DISTRO/setup.bash"
cd "$WS"
colcon build --symlink-install --packages-up-to rra_battery_protection
source "$WS/install/setup.bash"

ros2 topic info /uas1/mavlink_source >/dev/null
ros2 topic info /uas1/mavlink_sink >/dev/null

sudo install -m 0644 "$PKG_DIR/rra-power-shutdown.service" \
  /etc/systemd/system/rra-power-shutdown.service
sudo install -m 0644 "$PKG_DIR/config/rra-power-shutdown.env" \
  /etc/default/rra-power-shutdown
sudo systemctl daemon-reload
sudo systemctl enable --now rra-power-shutdown.service
sudo systemctl --no-pager --full status rra-power-shutdown.service
sudo journalctl -u rra-power-shutdown.service -n 30 --no-pager

echo "Instalado solo en DRY_RUN. No cambia la Matek y no ejecuta systemctl poweroff."
