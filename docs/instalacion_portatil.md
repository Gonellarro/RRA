# Tutorial · Instalar el entorno de software del RRA en el portátil

**Estado:** propuesta (2026-11-08). Desarrolla los pasos 2 a 6 de [`migracion_portatil.md`](migracion_portatil.md). Tareas: T-011, T-012 y T-013.

Desde ahora, **todo el trabajo de software del RRA se hace en el portátil**: simulación, estación de control, programas propios y, más adelante, ROS 2. En el PC de escritorio no se instala nada de esto. Allí solo quedan HQ y una copia del repo que se actualiza con `git pull`.

Cada bloque explica **qué se instala, para qué sirve y cuándo hace falta**. Hay que instalarlo en orden. No hace falta instalarlo todo hoy: las fases D y E esperan a su etapa.

---

## 1. El mapa: qué piezas hay y cómo se hablan

```text
                      MAVLink (TCP 5760 / UDP 14550)
 ┌──────────────────┐          ┌─────────────────────────────┐
 │ ArduRover SITL   │◄────────►│ MAVProxy (consola y mapa)   │
 │ (el "rover" en   │          ├─────────────────────────────┤
 │  el ordenador)   │◄────────►│ QGroundControl (estación)   │
 │                  │          ├─────────────────────────────┤
 │ Más adelante: la │◄────────►│ Programas Python del RRA    │
 │ H743 real por    │          │ (pymavlink, solo lectura)   │
 │ USB o telemetría │          ├─────────────────────────────┤
 └──────────────────┘          │ ROS 2 + MAVROS (etapa 7)    │
                               └─────────────────────────────┘
```

- **ArduRover** es el firmware que corre en la H743 del rover y decide motor, dirección, modos y failsafes.
- **SITL** (*Software In The Loop*) es ese mismo firmware compilado para correr en el portátil, con un vehículo y un GPS simulados. Permite aprender y probar sin hardware y sin riesgo.
- **MAVLink** es el idioma en que el autopiloto y los programas de tierra se intercambian mensajes (HEARTBEAT, posición, modo…). Todo lo de la derecha del dibujo habla MAVLink.
- Lo que funcione con SITL se conectará después, casi igual, a la placa real. Por eso el portátil también servirá de **estación de tierra** en las pruebas de campo.

| Fase | Qué | Para qué | Etapa del roadmap | Cuándo |
|---|---|---|---|---|
| A | Base del sistema, Git, SSH, repo | Trabajar con el repo compartido con el socio | 0 | Ahora |
| B | ArduPilot + SITL + MAVProxy + pymavlink | Simular el rover y hablarle | 1 | Ahora |
| C | QGroundControl | Estación de control gráfica | 1 (T-007) | Ahora o al hacer T-007 |
| D | Entorno Python del proyecto | Nuestros programas de lectura y logs | 2 (T-010) | Al empezar T-010 |
| E | Claude Code y flujo HQ | Trabajar con `/empezar` y `/cerrar` en el portátil | — (T-013) | Ahora |
| F | ROS 2, MAVROS, Gazebo | Laboratorio ROS | 7 | **No ahora** |

---

## 2. Paso 0 · Conocer el portátil (5 min)

Antes de instalar nada, en una terminal del portátil:

```bash
lsb_release -a                          # versión de Ubuntu
nproc                                   # hilos de CPU
free -h                                 # RAM
df -h ~                                 # disco libre en tu carpeta
lsblk -d -o NAME,ROTA,SIZE,MODEL        # ROTA=0 → SSD; ROTA=1 → disco mecánico
```

**Por qué:** la versión de Ubuntu decide qué ROS 2 se podrá instalar en la etapa 7 (ROS 2 Jazzy va con Ubuntu 24.04 y Lyrical Luth con **Ubuntu 26.04**). La RAM decide cuántos trabajos de compilación en paralelo se pueden lanzar. Apunta los resultados en el paso 0 de `migracion_portatil.md`.

> El portátil lleva **Ubuntu 26.04 LTS** (decisión del 2026-11-08). No pasa nada para las etapas 0–6: ArduPilot ya compila ahí (el PC de escritorio es 26.04). Para la etapa 7 se usará **ROS 2 Lyrical Luth**, la versión para Ubuntu 26.04, en lugar de Jazzy (decisión del socio, 2026-11-08).

---

## 3. Fase A · Base del sistema y repo (30 min)

### A.1 Actualizar e instalar lo básico

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y git curl build-essential openssh-server htop
```

| Paquete | Qué hace | Por qué lo necesitamos |
|---|---|---|
| `git` | Control de versiones | El repo RRA es el punto de encuentro con el socio y con el PC de escritorio. |
| `curl` | Descargar desde la terminal | Lo usan varios instaladores (Claude Code, scripts). |
| `build-essential` | Compilador de C/C++ (gcc, g++, make) | ArduPilot está escrito en C++ y SITL se compila en el portátil. |
| `openssh-server` | Permite entrar al portátil por SSH | Opcional, pero cómodo: desde el escritorio puedes mirar el portátil, copiar archivos o lanzar comandos sin moverte. |
| `htop` | Monitor de CPU y RAM | Vigilar la memoria mientras compila (8 GB van justos). |

### A.2 Identidad de Git

```bash
git config --global user.name "Martí Vich"
git config --global user.email "<tu correo de GitHub>"
git config --global pull.rebase true
```

**Por qué:** cada commit lleva autor. `pull.rebase true` hace que `git pull` coloque tus cambios encima de los del socio en lugar de crear commits de «merge» innecesarios.

### A.3 Clave SSH para GitHub

```bash
ssh-keygen -t ed25519 -C "portatil-rra"
cat ~/.ssh/id_ed25519.pub
```

Copia la línea que sale en GitHub → *Settings* → *SSH and GPG keys* → *New SSH key*, con un nombre como «Portátil RRA». Comprueba:

```bash
ssh -T git@github.com      # debe saludarte por tu usuario
```

**Por qué una clave nueva y no copiar la del escritorio:** si pierdes el portátil, revocas solo esa clave y el escritorio sigue funcionando.

### A.4 Clonar el repo

```bash
mkdir -p ~/Documentos/Personal
git clone git@github.com:Gonellarro/RRA.git ~/Documentos/Personal/RRA
```

**Por qué esta ruta:** es la misma que en el escritorio, así la documentación, los scripts y `CLAUDE.md` valen en los dos equipos.

> Ojo: el commit `f238957` (plan de migración) todavía está solo en el escritorio, sin subir. Hasta que se suba, este tutorial y `migracion_portatil.md` no estarán en el clon del portátil: tenlos abiertos en el escritorio o pásalos por SSH.

**Hecho cuando:** `cd ~/Documentos/Personal/RRA && git pull` funciona sin errores. Con esto se cierra la parte de base de la T-011.

---

## 4. Fase B · ArduPilot, SITL y MAVProxy (1–2 h, casi todo esperando)

### Dónde va cada cosa (decisión del 2026-11-08)

```text
~/Documentos/Personal/RRA/        ← el repo del proyecto (Git, compartido con el socio)
~/Herramientas/RRA/               ← herramientas de terceros del RRA, fuera del repo
    ├── ardupilot/                ← código de ArduPilot y SITL compilado
    │     └── .venv/              ← su entorno Python (MAVProxy, pymavlink…)
    ├── qgc/                      ← QGroundControl (fase C)
    └── (más adelante, el espacio de trabajo de ROS 2)
```

Lo nuestro, versionado; lo de terceros, aparte y reinstalable. ArduPilot no va dentro del repo porque es otro repositorio Git de 2 GB que el socio no necesita.

### B.1 Descargar el código de ArduPilot

```bash
mkdir -p ~/Herramientas/RRA && cd ~/Herramientas/RRA
git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git
cd ardupilot
```

**Qué es:** el código fuente de todos los firmwares de ArduPilot (Rover, Copter, Plane…). Los **submódulos** son librerías externas que necesita (MAVLink, DroneCAN, etc.). Sin `--recurse-submodules` no compila. Ocupa unos 2 GB.

### B.2 Elegir la versión (decisión pendiente con el socio)

```bash
git tag -l 'Rover-4.*' | sort -V | tail      # versiones estables de Rover
git checkout Rover-4.X.Y                     # la que acordéis
git submodule update --init --recursive      # submódulos de esa versión
```

**Por qué importa:** queremos simular **la misma versión de ArduRover que llevará la H743**, porque los parámetros y el comportamiento cambian entre versiones. Quien decide el firmware real es el responsable de hardware, así que hay que preguntárselo. Si aún no lo sabe, la propuesta es la última estable de Rover. La alternativa es el commit del escritorio (`eb8b5180a1`, rama de desarrollo, no una versión estable).

Elige la versión **antes** del paso B.3, porque las dependencias pueden cambiar de una versión a otra.

### B.3 Instalar las dependencias con el script oficial

```bash
cd ~/Herramientas/RRA/ardupilot
python3 -m venv --system-site-packages .venv    # el venv, dentro de la carpeta de ArduPilot
Tools/environment_install/install-prereqs-ubuntu.sh -y
```

**Por qué se crea antes el `.venv`:** el instalador busca primero un venv dentro de la carpeta de ArduPilot (`venv-ardupilot`, `venv` o `.venv`) y, si no lo encuentra, crea `~/venv-ardupilot` suelto en la carpeta personal. Creándolo antes, todo queda dentro de `~/Herramientas/RRA/ardupilot`. ArduPilot ya ignora `.venv` en su `.gitignore`. Comprobado en el instalador de la rama master (2026-10-15); si la versión elegida es más antigua, mirar en la salida del instalador la línea `Found existing venv at …`. Si dice `Creating new venv at ~/venv-ardupilot`, esa versión no lo soporta: no pasa nada, solo cambia la ruta.

Este script es el que el 2026-10-15 se interrumpió en el escritorio. Esta vez:

- portátil **enchufado**, sin otras aplicaciones abiertas;
- en otra terminal, `htop` para vigilar la RAM;
- **déjalo acabar aunque parezca parado**: algunos pasos (sobre todo compilar wxPython o descargar el compilador ARM) tardan muchos minutos sin escribir nada.

**Qué instala y para qué:**

| Pieza | Qué hace | Por qué la necesitamos |
|---|---|---|
| Paquetes de compilación (`g++`, `ccache`, `gawk`, `libtool`, librerías XML…) | Herramientas para compilar ArduPilot | SITL se compila desde el código. `ccache` hace que las recompilaciones sean mucho más rápidas. |
| Compilador ARM (`gcc-arm-none-eabi`, en `/opt`) | Compila firmware para placas reales con chip STM32, como la H743 | No hace falta para SITL. Es útil si algún día compilamos nosotros el firmware de la placa. Se puede saltar con `DO_AP_STM_ENV=0` delante del comando (ahorra ~1 GB). Propuesta: **instalarlo**, ocupa poco para lo que da. |
| Entorno Python `ardupilot/.venv` | Una «caja» Python aislada del sistema | Ubuntu no deja instalar paquetes Python en el sistema con `pip` (y no se debe). El venv guarda las herramientas de ArduPilot sin tocar el Python de Ubuntu. |
| **MAVProxy** (dentro del venv) | Estación de control en modo texto, con consola y mapa opcionales | Es la que lanza `sim_vehicle.py` por defecto. Sirve para ver el estado, cambiar modos, cargar misiones y repartir la conexión MAVLink a otros programas. |
| **pymavlink** (dentro del venv) | Librería Python para leer y enviar mensajes MAVLink | La usa MAVProxy y será la base de nuestro programa de lectura de la etapa 2. |
| wxPython, matplotlib, OpenCV… (dentro del venv) | Ventanas de consola, mapa y gráficas | Para `--console` y `--map` de MAVProxy y para analizar logs. |
| `empy`, `pexpect`, `future`, `lxml`… | Utilidades de los scripts de ArduPilot | Generan código MAVLink durante la compilación y controlan SITL desde `sim_vehicle.py`. |
| Líneas en `~/.profile` | Añaden `Tools/autotest` y `ccache` al PATH y activan el venv al entrar | Para poder escribir `sim_vehicle.py` desde cualquier carpeta. **Esto es lo que faltó en el escritorio.** |

**Comprobación al acabar:**

```bash
tail -n 15 ~/.profile          # deben aparecer el PATH de autotest y el source del venv
. ~/.profile                   # o cerrar la sesión y volver a entrar
which sim_vehicle.py           # debe dar ~/Herramientas/RRA/ardupilot/Tools/autotest/sim_vehicle.py
which mavproxy.py              # debe estar dentro de ~/Herramientas/RRA/ardupilot/.venv
python -c "import pymavlink; print(pymavlink.__version__)"
```

Si `~/.profile` no tiene esas líneas, el script no terminó: vuelve a lanzarlo (es seguro repetirlo).

### B.4 Compilar SITL de Rover

```bash
cd ~/Herramientas/RRA/ardupilot
./waf configure --board sitl
./waf rover -j4
```

**Qué hace:** `waf` es el sistema de compilación de ArduPilot. `--board sitl` indica que el destino es el propio ordenador y no una placa. `rover` compila solo ArduRover. `-j4` limita a 4 compilaciones en paralelo, para no quedarse sin memoria con 8 GB. El resultado es `build/sitl/bin/ardurover`. La primera vez tarda 10–20 min; las siguientes, mucho menos gracias a `ccache`.

### B.5 Primer arranque y verificación (criterio del paso 5 de la migración)

```bash
cd ~/Herramientas/RRA/ardupilot/Rover
sim_vehicle.py -v Rover --console --map -w
```

**Qué hace:** `sim_vehicle.py` arranca el binario SITL y MAVProxy, y los conecta. `-v Rover` elige el vehículo, `--console` y `--map` abren las ventanas, y `-w` borra los parámetros guardados y arranca con los de fábrica (solo la primera vez o para reiniciar desde cero).

En la consola de MAVProxy (todo en simulación, **sin armar y sin misiones**):

- [ ] Arranca y MAVProxy se conecta por `127.0.0.1:5760`; recibe ~1.300 parámetros.
- [ ] Se ven la consola y el mapa.
- [ ] `mode HOLD` y `mode MANUAL` cambian el modo.
- [ ] `status HEARTBEAT` y `status GPS_RAW_INT` responden.
- [ ] Se sale con `Ctrl+C` (o cerrando la terminal) y se vuelve a arrancar sin `-w`.

**Hecho cuando:** todas las casillas están marcadas. Con esto se cierra la T-012.

---

## 5. Fase C · QGroundControl (30 min)

**Qué es:** una estación de control gráfica (mapa, instrumentos, planificador de misiones, parámetros). El roadmap propone Mission Planner o QGroundControl; Mission Planner es de Windows, así que en Linux toca **QGroundControl (QGC)**. La decisión final de si hace falta o basta MAVProxy es la T-007; instalarlo no estorba.

```bash
sudo usermod -aG dialout "$(id -un)"
sudo systemctl mask --now ModemManager.service
sudo apt install -y gstreamer1.0-plugins-bad gstreamer1.0-libav gstreamer1.0-gl \
                    libxcb-xinerama0 libxkbcommon-x11-0 libxcb-cursor0
sudo apt install -y libfuse2t64 || sudo apt install -y libfuse2
```

Después, descarga `QGroundControl-x86_64.AppImage` desde la [guía oficial de instalación](https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html), y:

```bash
mkdir -p ~/Herramientas/RRA/qgc && mv ~/Descargas/QGroundControl-x86_64.AppImage ~/Herramientas/RRA/qgc/
chmod +x ~/Herramientas/RRA/qgc/QGroundControl-x86_64.AppImage
```

Cierra la sesión y vuelve a entrar (para que valga el grupo `dialout`).

| Paso | Por qué |
|---|---|
| Grupo `dialout` | Da permiso para usar puertos serie (`/dev/ttyACM0`, `/dev/ttyUSB0`). Es como se verá la H743 por USB o una radio de telemetría. Sin él, solo funcionaría con `sudo`. |
| Desactivar **ModemManager** | Es un servicio de Ubuntu que busca módems 3G/4G y «prueba» cualquier puerto serie que aparezca. Se queda la H743 durante unos segundos y estropea la conexión. Probablemente es el aviso de ModemManager que salió en el primer arranque (T-008). |
| GStreamer | QGC lo usa para mostrar vídeo. Sin vídeo no hace falta, pero sin estas librerías QGC da errores al arrancar. |
| `libfuse2` / `libxcb…` | Necesarios para ejecutar AppImages y para las ventanas Qt de QGC. En Ubuntu 24.04 y posteriores el paquete se llama `libfuse2t64`. |
| AppImage en `~/Herramientas/RRA/qgc` | QGC se distribuye como un solo archivo ejecutable: no ensucia el sistema y para quitarlo basta con borrarlo. |

**Probar con SITL:** arranca SITL como en B.5 y después abre QGC (`~/Herramientas/RRA/qgc/QGroundControl-x86_64.AppImage`). `sim_vehicle.py` reenvía MAVLink a UDP 14550, que es donde QGC escucha por defecto, así que debería conectarse solo y mostrar el rover en el mapa.

---

## 6. Fase D · Entorno Python del proyecto (cuando empiece la T-010)

Para nuestros propios programas (lectura de estado y logs, etapa 2), la propuesta es un **venv propio dentro del repo**, separado del de ArduPilot:

```bash
sudo apt install -y python3-venv
cd ~/Documentos/Personal/RRA
python3 -m venv .venv
. .venv/bin/activate
pip install pymavlink
pip freeze > requirements.txt      # versiones exactas, versionadas en Git
```

**Por qué separado:** el venv de ArduPilot lo gestiona su script y puede cambiar al actualizar ArduPilot. El nuestro fija sus propias versiones en `requirements.txt` y el socio, o cualquiera, lo puede reproducir con `pip install -r requirements.txt`. `.venv/` ya está en `.gitignore`, así que no se sube. Esto se confirmará al empezar la T-010.

**Regla:** nunca `sudo pip install`. Todo paquete Python, dentro de un venv.

---

## 7. Fase E · Claude Code y flujo HQ (T-013)

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Qué es:** el mismo asistente que usas en el escritorio, para trabajar en el portátil con `/empezar` y `/cerrar`.

Después hay que copiar desde el escritorio los comandos de la metodología, por SSH (con `openssh-server` del paso A.1):

```bash
# desde el PC de escritorio
scp -r ~/.claude/skills/empezar ~/.claude/skills/cerrar marti@<ip-del-portátil>:~/.claude/skills/
```

Queda un problema pendiente, descrito en el paso 6 de `migracion_portatil.md`: `CLAUDE.md` apunta a `/home/marti/HQ/docs/METODOLOGIA.md`, que en el portátil no existe. La propuesta recomendada es dar un commit y un remoto privado a HQ y clonarlo también en el portátil.

**Ciclo de trabajo desde ahora:**

| Dónde | Al empezar | Al acabar |
|---|---|---|
| Portátil | `git pull` → `/empezar` | `/cerrar` → commit → `git push` |
| Escritorio | — | `git pull` en RRA para que el panel HQ lo vea. **No editar RRA aquí.** |

---

## 8. Fase F · Lo que NO se instala todavía (y por qué)

| Pieza | Para qué servirá | Por qué esperar |
|---|---|---|
| **ROS 2 Lyrical Luth** (la de Ubuntu 26.04; sustituye a Jazzy) | Marco para robots: nodos, topics, mapas (etapa 7) | El roadmap lo deja para cuando SITL, la lectura de estado y las misiones AUTO funcionen. Añadirlo antes complica el aprendizaje sin dar nada a cambio. Ocupa varios GB. |
| **MAVROS 2** o el DDS nativo de ArduPilot | Puente entre MAVLink y ROS 2 | Depende de ROS 2. Se compararán en la etapa 7. |
| **Gazebo** | Simulador 3D con física y sensores | Solo hará falta si se prueba navegación local con sensores (etapa 8). Es pesado para 8 GB de RAM. |
| **Nav2** | Navegación local con ROS 2 | Etapa 8, y solo si demuestra una mejora. |

Cuando llegue la etapa 7 se comprobará la versión de ROS 2 compatible con el Ubuntu del portátil y se escribirá su propio tutorial.

---

## 9. Espacio en disco aproximado

| Qué | Tamaño |
|---|---|
| Ubuntu y paquetes base | ~15 GB |
| `~/Herramientas/RRA/ardupilot` (código + compilación SITL) | ~2–3 GB |
| `ardupilot/.venv` | ~1,5 GB |
| Compilador ARM en `/opt` | ~1 GB |
| QGroundControl | ~0,2 GB |
| Margen para logs y, más adelante, ROS 2 + Gazebo | 20–30 GB |

Con 256 GB sobra.

---

## 10. Lista final

- [ ] Paso 0: datos del portátil apuntados (Ubuntu, SSD, RAM).
- [ ] A: `git pull` funciona en `~/Documentos/Personal/RRA`.
- [ ] B: versión de ArduPilot acordada con el socio; SITL pasa la verificación de B.5.
- [ ] C: QGC conecta con SITL (o queda aplazado a la T-007).
- [ ] E: Claude Code instalado; `/empezar` funciona en el portátil.
- [ ] Versiones reales anotadas en `docs/entorno_de_desarrollo.md` (T-003).
- [ ] Entrada en el devlog con el resultado.

## Referencias

- [ArduPilot: preparar el entorno en Linux](https://ardupilot.org/dev/docs/building-setup-linux.html)
- [ArduPilot: SITL](https://ardupilot.org/dev/docs/sitl-simulator-software-in-the-loop.html)
- [ArduPilot: usar SITL con estaciones de control](https://ardupilot.org/dev/docs/using-sitl-for-ardupilot-testing.html)
- [MAVProxy](https://ardupilot.org/mavproxy/)
- [QGroundControl: descarga e instalación](https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html)
- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview)

Los comandos y nombres de paquetes se han escrito según la documentación conocida hasta la fecha. Si alguno falla en el portátil, apunta el error en el devlog y se corrige este documento.
