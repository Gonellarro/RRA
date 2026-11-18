# Evidencias seleccionadas: Pololu, 18-11-2026

- `power-pololu-repeat-20261118.log` y `.jsonl`: segunda prueba de la Matek con tensión simulada de 7,1 V, petición MAVLink y apagado real del Companion. El usuario confirmó el corte del Pololu y el encendido posterior a la primera.
- `pololu-test-poweroff-journal-20261118.txt`: fragmento del journal de la primera prueba real, anterior a la repetición. En esa prueba el usuario observó un segundo corte al volver a encender; su causa no quedó determinada.

Los archivos se comparten sin alterar. La tensión de prueba es simulada; no son registros de una descarga real. El journal de la segunda prueba se revisó en la Orange Pi y confirmó `poweroff.target`, pero no se guardó una copia completa en esta carpeta.
