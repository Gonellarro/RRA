#!/usr/bin/env bash
# Diagnóstico de lectura del companion; no modifica la configuración.
set -u

printf '\n== Sistema ==\n'
hostname
uname -smr
if [ -r /etc/os-release ]; then
    . /etc/os-release
    printf 'Sistema: %s\n' "${PRETTY_NAME:-desconocido}"
fi
if [ -r /etc/armbian-release ]; then
    . /etc/armbian-release
    printf 'Armbian: %s\n' "${VERSION:-desconocida}"
fi

printf '\n== Recursos ==\n'
uptime
free -h
df -h /
found_temperature=0
for sensor in /sys/class/thermal/thermal_zone*/temp; do
    [ -r "$sensor" ] || continue
    value=$(cat "$sensor")
    case "$value" in
        ''|*[!0-9]*) continue ;;
    esac
    printf '%s: %d.%03d °C\n' "$sensor" "$((value / 1000))" "$((value % 1000))"
    found_temperature=1
done
[ "$found_temperature" -eq 1 ] || printf 'Temperatura: no disponible\n'

printf '\n== ROS 2 ==\n'
printf 'Distribución activa: %s\n' "${ROS_DISTRO:-no cargada}"
if command -v ros2 >/dev/null 2>&1; then
    printf 'Ejecutable: %s\n' "$(command -v ros2)"
else
    printf 'Ejecutable: no disponible en esta sesión\n'
fi
if command -v colcon >/dev/null 2>&1; then
    printf 'colcon: disponible\n'
else
    printf 'colcon: no disponible en esta sesión\n'
fi
printf 'Workspace: %s\n' "${HOME}/rra_ws"
if [ -d "${HOME}/rra_ws/src" ]; then
    printf 'Directorio src: disponible\n'
else
    printf 'Directorio src: no disponible\n'
fi
