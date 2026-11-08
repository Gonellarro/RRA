# Migración del entorno de desarrollo al portátil

**Estado:** propuesta (2026-11-08). Tareas: T-011 a T-014 de `seguimiento/TAREAS.md`.

## Por qué

Las herramientas del rover (ArduPilot SITL, estación de control y, más adelante, ROS 2) instalan muchos paquetes del sistema. Se llevan a un portátil dedicado para no ensuciar el PC principal, que se queda con HQ y el trabajo diario.

## Reparto de papeles

| Equipo | Qué hace |
|---|---|
| **Portátil (laboratorio)** | ArduPilot, SITL, estación de control, scripts del proyecto y, más adelante, ROS 2. Aquí se trabaja en RRA, con Claude Code y `/empezar` / `/cerrar`. |
| **PC principal** | HQ (panel y metodología) y una copia del repo RRA que **solo se actualiza con `git pull`** para que el panel la vea. No se edita aquí. |
| **GitHub** (`Gonellarro/RRA`) | Punto de encuentro: portátil, PC principal y socio. |

Regla de oro, igual que con el socio: **`git pull --rebase` al empezar, commit y `git push` al cerrar.**

## Punto de partida (PC principal, 2026-11-08)

| Elemento | Valor |
|---|---|
| SO | Ubuntu 26.04 LTS, Python 3.14.4, Git 2.53.0 |
| ArduPilot | `~/src/ardupilot`, commit `eb8b5180a1` (`ArduPilot-4.6.0-beta1-9293-geb8b5180a1`, rama master del 2026-10-15), con submódulos |
| Tamaño | `~/src/ardupilot` 2,1 GB · `~/venv-ardupilot` 1,4 GB |
| venv | `~/venv-ardupilot`: MAVProxy 1.8.75, pymavlink 2.4.50 |
| SITL | `build/sitl/bin/ardurover`; se conecta por `tcp:127.0.0.1:5760` |
| Particularidad | El instalador se interrumpió y no escribió el PATH ni el `source` del venv en `~/.profile` |

## Paso 0 · Datos del portátil (antes de tocar nada)

Apuntar en este documento:

- modelo, CPU (núcleos), RAM y disco libre;
- si tiene SSD;
- sistema operativo actual y si se puede borrar entero.

**Datos (2026-11-08):** Intel Core i5 de 8.ª generación (4 núcleos / 8 hilos), **8 GB de RAM**, **256 GB de disco**. Pendiente: si es SSD y qué SO tiene ahora. Cumple los mínimos. Con 8 GB, compilar con `-j4` para no quedarse sin memoria, y no usar el portátil para otra cosa mientras instala.

Mínimos orientativos: **8 GB de RAM** (con 4 GB se compila, pero lento y con `-j2`), **40 GB libres** (ArduPilot y venv ocupan unos 4 GB; ROS 2 y Gazebo, más adelante, bastante más) y SSD si es posible.

## Paso 1 · Sistema operativo

**Decisión pendiente** (se apunta en el devlog al tomarla):

- **Ubuntu 24.04 LTS.** Es la plataforma principal de ROS 2 Jazzy, que es el que cita el README para la etapa 7. ArduPilot la soporta. *Propuesta recomendada.*
- **Ubuntu 26.04 LTS.** Es igual que el PC principal y ya se ha visto que ArduPilot compila en él. Antes de elegirla hay que comprobar qué ROS 2 está soportado en 26.04.

Instalación limpia, con usuario `marti` para que las rutas coincidan con las del PC principal.

## Paso 2 · Base del sistema

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y git curl openssh-server build-essential
git config --global user.name "Martí Vich"
git config --global user.email "<tu correo>"
```

- **Acceso a GitHub:** clave SSH nueva para el portátil (`ssh-keygen -t ed25519`), dada de alta en GitHub. Es mejor que copiar la del PC principal, porque así se puede revocar por separado.
- **SSH desde el PC principal** (opcional, pero cómodo): permite mirar el portátil o copiar archivos sin moverse.

## Paso 3 · Repo del proyecto

```bash
mkdir -p ~/Documentos/Personal
git clone git@github.com:Gonellarro/RRA.git ~/Documentos/Personal/RRA
cd ~/Documentos/Personal/RRA
git config pull.rebase true
```

La misma ruta que en el PC principal, para que la documentación y los scripts sirvan en los dos.

## Paso 4 · ArduPilot y SITL

```bash
mkdir -p ~/src && cd ~/src
git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git
cd ardupilot
```

**Decisión pendiente, la versión:**
- **Mismo commit que el PC principal** (`git checkout eb8b5180a1 && git submodule update --init --recursive`). Repite exactamente lo que ya funciona.
- **La última versión estable de Rover** (una etiqueta `Rover-4.x.y`). Es lo más parecido a lo que se cargará en la H743 y es más coherente con la etapa 5. *Propuesta recomendada*, pero hay que confirmarla con el socio, porque la versión real del firmware la decide el hardware.

Instalación de dependencias, con cuidado para que no se repita el bloqueo:

```bash
Tools/environment_install/install-prereqs-ubuntu.sh -y
```

- Lanzarla con el portátil enchufado, sin otras aplicaciones abiertas y vigilando la RAM (`free -h`).
- Al acabar, **comprobar que ha escrito** en `~/.profile` el PATH a `Tools/autotest` y el `source ~/venv-ardupilot/bin/activate`. Después cerrar la sesión y volver a entrar, o hacer `. ~/.profile`.

Compilación:

```bash
./waf configure --board sitl
./waf rover -j4        # 8 GB de RAM: limitar a 4 trabajos
```

## Paso 5 · Verificación (criterio para dar la migración por buena)

Hay que repetir lo del diario del 2026-10-15:

```bash
cd ~/src/ardupilot/Rover
sim_vehicle.py -v Rover --console --map -w
```

- [ ] Compila sin errores y arranca.
- [ ] MAVProxy se conecta por `127.0.0.1:5760` y recibe unos 1.292 parámetros (puede variar si cambia la versión).
- [ ] Se ven la consola y el mapa.
- [ ] `mode HOLD` y `mode MANUAL` cambian el modo.
- [ ] `status HEARTBEAT` y `status GPS_RAW_INT` responden.
- [ ] Se ha parado SITL de forma limpia y se ha vuelto a arrancar.

Todo en simulación: sin armar el vehículo y sin misiones.

## Paso 6 · Flujo de trabajo HQ en el portátil

- Instalar Claude Code.
- Copiar los comandos `/empezar` y `/cerrar` desde el PC principal:
  `scp -r ~/.claude/skills/empezar ~/.claude/skills/cerrar <portátil>:~/.claude/skills/`
- **Problema:** `CLAUDE.md` apunta a `/home/marti/HQ/docs/METODOLOGIA.md`, que en el portátil no existe. El código de HQ tampoco tiene ningún commit ni remoto, así que no se puede clonar. Opciones:
  - **a)** Dar a HQ un primer commit y un repo remoto privado, y clonarlo también en el portátil. Así queda resuelto este problema y además HQ deja de estar sin copia. *Propuesta recomendada.*
  - **b)** Copiar solo `METODOLOGIA.md` a la misma ruta del portátil. Es más rápido, pero hay que acordarse de recopiarlo cuando cambie.
- `/empezar` usa `hq preparar`, pero solo para preparar una carpeta nueva. RRA ya está preparado, así que en el portátil no hace falta.

## Paso 7 · Sincronización con el panel HQ

- En el portátil, cada `/cerrar` termina con commit y `git push` (devlog, ESTADO y TAREAS incluidos).
- En el PC principal, `git pull` en `~/Documentos/Personal/RRA` antes de mirar el panel.
- Más adelante se puede automatizar ese `pull` con un temporizador de systemd o con cron (sería una tarea nueva, si hace falta).
- Desde la migración, en el PC principal **no se edita RRA**, para evitar conflictos con uno mismo.

## Paso 8 · Documentar

- Actualizar `docs/entorno_de_desarrollo.md` con el entorno del **portátil**, que pasa a ser el de referencia (es la T-003).
- Entrada en el devlog con el resultado de la verificación del paso 5.

## Paso 9 · Limpiar el PC principal (opcional, al final)

**Solo cuando el paso 5 haya funcionado en el portátil** y tras confirmarlo de nuevo:

- borrar `~/src/ardupilot` (2,1 GB) y `~/venv-ardupilot` (1,4 GB);
- `~/.mavproxy` y `~/.tilecache` (4 MB) se pueden borrar o dejar;
- los paquetes de `apt` que instaló `install-prereqs` son difíciles de separar de los demás y no se tocan, salvo que se decida otra cosa.

Antes de borrar, guardar en el repo `Rover/mav.parm` del primer arranque como parametría de partida (enlaza con T-006).
