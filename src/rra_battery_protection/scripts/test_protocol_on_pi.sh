#!/usr/bin/env bash
set -eo pipefail

WS="${RRA_WS:-$HOME/rra_ws}"
ROS_DISTRO="${ROS_DISTRO:-lyrical}"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-205}"
export ROS_AUTOMATIC_DISCOVERY_RANGE="${ROS_AUTOMATIC_DISCOVERY_RANGE:-LOCALHOST}"
export RRA_POWER_SHUTDOWN_DRY_RUN=1
EVENT_LOG="${TMPDIR:-/tmp}/rra-battery-protection-smoke.jsonl"
LISTENER_LOG="${TMPDIR:-/tmp}/rra-battery-protection-listener.log"
rm -f "$EVENT_LOG" "$LISTENER_LOG"

source "/opt/ros/$ROS_DISTRO/setup.bash"
source "$WS/install/setup.bash"
ros2 run rra_battery_protection rra-power-shutdown --ros-args \
  -p event_log:="$EVENT_LOG" >"$LISTENER_LOG" 2>&1 &
LISTENER_PID=$!
cleanup() {
  kill -INT "$LISTENER_PID" 2>/dev/null || true
  wait "$LISTENER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

ready=0
for _ in $(seq 1 50); do
  if ! kill -0 "$LISTENER_PID" 2>/dev/null; then
    cat "$LISTENER_LOG"
    echo "Listener exited before the handshake" >&2
    exit 1
  fi
  if ros2 node list 2>/dev/null | grep -q '^/rra_power_shutdown$'; then
    ready=1
    break
  fi
  sleep 0.2
done
if [[ "$ready" != 1 ]]; then
  cat "$LISTENER_LOG"
  echo "Listener did not become ready" >&2
  exit 1
fi

timeout 12s ros2 run rra_battery_protection rra-power-shutdown-protocol-smoke
sleep 3
cat "$LISTENER_LOG"
cat "$EVENT_LOG"
grep -q 'DRY_RUN: poweroff simulado' "$LISTENER_LOG"
grep -q '"nonce":12345' "$EVENT_LOG"
echo "PASS: synthetic ROS/MAVLink handshake completed; Linux stayed on."
