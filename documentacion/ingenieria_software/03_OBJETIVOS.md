# 4. Objetivos

## 4.1 Objetivo general

Diseñar e implementar una plataforma de recaudo digital con códigos QR firmados para el transporte público de Ibagué, que permita validar flujos de pago, traspaso y conciliación de turnos con trazabilidad de requisitos y pruebas automatizadas.

## 4.2 Objetivos específicos

1. Implementar la autenticación y autorización por roles (pasajero y conductor) mediante tokens bearer firmados con HMAC.
2. Modelar el dominio de transporte (usuarios, roles, rutas, tarifas, turnos, pagos, viajes, QR y transbordos) en SQLAlchemy.
3. Construir una API REST con validaciones de entrada y salida mediante DTOs Pydantic.
4. Desarrollar una interfaz web adaptable (PWA) que consuma la API y muestre respuestas y errores de forma intuitiva.
5. Garantizar propiedades ACID en las transacciones de débito, recarga y pago.
6. Aplicar tarifas dinámicas según ruta, día hábil, fin de semana y festivo colombiano.
7. Validar el flujo de integración completo (pantalla → JavaScript → API → backend → base de datos) con casos exitosos y de error.
8. Documentar la arquitectura, los casos de uso, las pruebas y la trazabilidad de requisitos bajo normas APA 7.

## Referencias

- Pressman, R. S., & Maxim, B. R. (2020). *Software engineering: A practitioner's approach* (9.ª ed.). McGraw-Hill.