# Guardado local de continuidad

Solicitud del usuario: 2026-11-04. Se prepara una copia local comprimida en
`C:\RRA_BACKUPS\2026-11-04_0324`, sin commit ni push. Consultar el manifiesto
de esa carpeta para ver qué archivos se copiaron y el resultado de verificación.

La copia comprende el árbol de `C:\RRA` con su metadata Git y cambios sin
commit, el entorno local `~/rra-sitl` de WSL y una copia de los fuentes y
herramientas del workspace de la Orange Pi. La clave privada SSH y contraseñas
quedan fuera de la copia. La copia no incluye una imagen completa de la Orange
Pi ni la configuración instalada de Armbian/ROS; reconstruirla requiere seguir
la documentación y volver a verificar versiones y accesos.

Los archivos SITL y DataFlash contienen datos de simulación. No confundirlos
con mediciones reales del rover. Para restaurar, inspeccionar primero la copia
y extraerla a una carpeta nueva; no sobrescribir el proyecto o el workspace
existente sin revisar y comparar los cambios. Los entornos y claves SSH no se
reconstruyen automáticamente. No publicar ni sincronizar esta copia.
