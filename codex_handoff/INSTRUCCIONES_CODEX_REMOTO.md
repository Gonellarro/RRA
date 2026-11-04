# Continuar desde Codex Remoto

1. En la aplicación móvil, abre Remote y selecciona el portátil conectado y
   el **checkout existente `C:\RRA`**, no una copia nueva. Mantén el portátil
   encendido y conectado. La [guía oficial de OpenAI](https://developers.openai.com/blog/mastering-codex-remote-for-engineering)
   explica la selección de host y workspace. Si la interfaz no ofrece esa ruta,
   no asumas que otro checkout contiene los cambios: informa al usuario.
2. Lee `C:\RRA\codex_handoff\CONTEXTO_RRA.md`, `ESTADO_ACTUAL.md` y
   `PLAN_SIGUIENTES_PASOS.md`; después `README.md`, `Roadmap_RRA_Software.md`,
   `docs/diario.md` y `docs/companion_orange_pi.md`. Conserva sus cambios sin
   commit. La presencia de esta carpeta no demuestra que Remote pueda acceder:
   compruébalo en la nueva sesión.
3. En PowerShell, ejecuta `Set-Location C:\RRA` y consulta
   `git status --short --branch` y `git diff`. La rama esperada es
   `feature/orangepi-ros2`. No crees ramas, commits, PR ni hagas push; no
   modifiques el remoto ni sincronices la transferencia con servicios externos.
4. Comprueba SSH sin contraseña en el chat:

   ```powershell
   ssh -i "$env:USERPROFILE\.ssh\rra_orangepi_ed25519" -o BatchMode=yes -o ConnectTimeout=8 rra@192.168.1.156 "hostname"
   ```

   La clave privada permanece en el perfil Windows, fuera del repositorio. La
   IP es DHCP y puede cambiar. Si falla, informa y diagnostica; no pidas que se
   escriba la contraseña en el chat ni cambies red, SSH o claves sin autorización.
   Root quedó disponible como respaldo, no como usuario ordinario.
5. Para diagnóstico, entra con el mismo comando SSH sin `"hostname"` y ejecuta
   `bash ~/rra_ws/tools/companion_diagnostico.sh`. En una sesión interactiva
   `echo "$ROS_DISTRO"` debe mostrar `lyrical`. Para una ejecución remota no
   interactiva carga explícitamente `source /opt/ros/lyrical/setup.bash` antes
   del diagnóstico; de lo contrario puede indicar que ROS no está cargado.
6. ArduRover SITL ya se ha conectado mediante un puente de un solo sentido con
   MAVROS en la Orange Pi; leer `sitl/README.md` y `ESTADO_ACTUAL.md` para
   versiones, fallos y límites. Se corrigió el monitor de batería solo en SITL,
   se probaron rosbag y tres cierres, y se ampliaron diagnósticos. La fase 3 ha
   demostrado dos misiones AUTO y una parada en SITL; consultar
   `sitl/FASE3_MISION_SITL.md`. El siguiente bloque es la etapa 4 de fallos y
   autoridad, sin presuponer validación del hardware ni aislamiento de MAVROS.
7. Al finalizar cada sesión, actualiza el estado y el plan **en esta carpeta
   local**, con fechas, comandos, versiones, pruebas, fallos y límites. No
   modifiques documentos compartidos con Martín sin autorización. Esta carpeta
   se excluye mediante `.git/info/exclude`, que solo afecta a este clon; no
   garantiza protección ante `git add -f` o servicios de sincronización.

No alteres configuración de red/SSH, contraseñas o claves; no formatees ni
cambies particiones, kernel o firmware sin autorización. No enciendas motores ni
emitas comandos de vehículo. Pide al usuario decisiones críticas o destructivas,
no confirmación para cada lectura o paso rutinario autorizado.
