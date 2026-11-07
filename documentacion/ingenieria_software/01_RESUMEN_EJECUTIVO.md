# 2. Resumen ejecutivo

## 2.1 Descripción breve del proyecto

QrPass es un prototipo funcional de plataforma de pago y recaudo digital para el transporte público de Ibagué. El sistema permite que un pasajero consulte rutas y tarifas, gestione una billetera virtual, realice pagos mediante el escaneo del código QR que muestra el bus y consulte su historial de viajes. De forma paralela, el conductor inicia un turno, genera un QR temporal firmado, registra pagos manuales y cierra el turno con conciliación de efectivo (Hernández & Pressman, 2021; Sommerville, 2016).

La solución se compone de una interfaz web adaptable y progresiva (PWA) y de una API REST construida con FastAPI, SQLAlchemy 2 y Pydantic. Los datos se persisten en SQLite durante el desarrollo y la demostración. Todas las operaciones son de demostración: no se procesa dinero real ni se integran pasarelas bancarias.

## 2.2 Objetivo general

Desarrollar un prototipo de sistema de recaudo digital basado en códigos QR firmados que permita validar el flujo completo de pago, traspaso y conciliación de turnos en el transporte público de Ibagué, con trazabilidad de requisitos y evidencia de pruebas automatizadas.

## 2.3 Alcance

**Dentro del alcance (demostración):**

- Registro y autenticación de pasajeros y conductores con roles.
- Billetera virtual, recargas ficticias e idempotentes y consulta de saldo.
- Pago de pasaje mediante escaneo del QR del bus (firma HMAC, vigencia y asociación al turno).
- Pago manual simulado en efectivo o tarjeta.
- Traspaso único a otra ruta dentro de 20 minutos.
- Tarifa dinámica por ruta, día hábil, fin de semana y festivo colombiano.
- Historial de viajes y movimientos.
- Gestión de turnos del conductor: inicio, registro de pagos, generación de QR y cierre con conciliación.
- Documentación de ingeniería de software, arquitectura, UML y trazabilidad.

**Fuera del alcance (pendiente para producción):**

- Procesamiento de dinero real y pasarelas POS/bancarias.
- Sincronización offline operativa por lotes.
- Firma asimétrica para validadores sin conexión.
- Migraciones versionadas sobre base productiva.
- Pruebas de concurrencia, carga y seguridad avanzada.

## 2.4 Público objetivo

El sistema se orienta a tres actores: pasajeros (usuarios finales del servicio), conductores (operadores del bus) y personal técnico/administrativo encargado de la operación y el soporte. La documentación y las cuentas de demostración permiten que jurados, docentes y nuevos desarrolladores comprendan y validen el prototipo sin conocimiento previo del dominio.

## Referencias

- Hernández, R. K., & Pressman, R. S. (2021). *Software engineering: A practitioner's approach* (9.ª ed.). McGraw-Hill.
- Sommerville, I. (2016). *Software engineering* (10.ª ed.). Pearson.