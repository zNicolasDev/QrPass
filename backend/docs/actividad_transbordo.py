"""Implementacion independiente de la actividad de transbordo.

El pasajero usa el proceso para corregir un abordaje en el bus equivocado.
Las reglas son didacticas y no consultan la base de datos del backend.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Viaje:
    id: int
    pasajero: str
    ruta_origen: str
    fecha: datetime
    ruta_destino: str | None = None


class ServicioTransbordo:
    """Comprueba las condiciones y actualiza el destino del viaje."""

    def __init__(self, viajes, rutas_activas):
        self.viajes = viajes
        self.rutas_activas = rutas_activas

    def corregir(self, pasajero, viaje_id, ruta_destino, ahora=None):
        print("ServicioTransbordo: buscando el viaje seleccionado")
        viaje = next((item for item in self.viajes if item.id == viaje_id), None)
        if viaje is None:
            raise ValueError("El viaje no existe.")
        if viaje.pasajero != pasajero:
            raise ValueError("El viaje pertenece a otro pasajero.")
        if viaje.ruta_destino is not None:
            raise ValueError("El viaje ya fue corregido.")

        momento = ahora or datetime.now()
        if momento - viaje.fecha > timedelta(minutes=20):
            raise ValueError("Se vencio el plazo de 20 minutos.")
        if ruta_destino not in self.rutas_activas:
            raise ValueError("La ruta de destino no esta activa.")
        if ruta_destino == viaje.ruta_origen:
            raise ValueError("Selecciona una ruta diferente a la de origen.")

        viaje.ruta_destino = ruta_destino
        print("ServicioTransbordo: viaje actualizado sin generar otro cobro")
        return viaje


def ejecutar():
    rutas_activas = {"Ruta Norte", "Ruta Centro", "Ruta Sur"}
    viajes = [
        Viaje(1, "Ana", "Ruta Norte", datetime.now()),
        Viaje(2, "Ana", "Ruta Centro", datetime.now() - timedelta(minutes=30)),
    ]
    servicio = ServicioTransbordo(viajes, rutas_activas)

    print("\n--- Escenario exitoso: bus equivocado ---")
    corregido = servicio.corregir("Ana", 1, "Ruta Centro")
    print(f"Viaje {corregido.id}: {corregido.ruta_origen} -> {corregido.ruta_destino}")

    print("\n--- Escenario alternativo: tiempo vencido ---")
    try:
        servicio.corregir("Ana", 2, "Ruta Sur")
    except ValueError as error:
        print(f"Transbordo rechazado: {error}")


if __name__ == "__main__":
    ejecutar()
