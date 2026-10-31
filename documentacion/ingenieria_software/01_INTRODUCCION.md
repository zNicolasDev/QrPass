# 1. INTRODUCCIÓN

## 1.1. Generalidades
QrPass es un prototipo funcional que digitaliza el proceso de abordaje y recaudo en transporte público mediante códigos QR. Combina una API REST desarrollada con FastAPI, una interfaz web tipo PWA para pasajero y conductor, y un esquema de datos relacional basado en SQLAlchemy con SQLite para entorno de demostración.

## 1.2. Justificación
El recaudo manual presenta dificultades en el control, trazabilidad y agilidad del proceso. QrPass registra cada abordaje como un Pago + Viaje, controla el turno del conductor, habilita el uso de QR firmado y mantiene la integridad entre saldo, recaudo y transbordos.

## 1.3. Objetivo General
Documentar técnica y metodológicamente el sistema QrPass, describiendo su arquitectura, modelo de datos, reglas de negocio, funcionalidades implementadas, pruebas y forma de despliegue.

## 1.4. Objetivos Específicos
- Identificar actores, requisitos funcionales y no funcionales.
- Modelar el dominio con diagramas UML.
- Documentar el modelo entidad-relación y diccionario de datos.
- Describir la arquitectura por capas.
- Evidenciar las pruebas automatizadas existentes.
- Generar matriz de trazabilidad entre requisitos, casos de uso, endpoints y pruebas.
