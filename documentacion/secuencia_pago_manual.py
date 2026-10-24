"""Implementacion independiente de la secuencia de pago manual.

Representa el pago en efectivo o tarjeta del diagrama de secuencia 1.
Se ejecuta con Python sin paquetes externos y no usa el backend.
"""

from dataclasses import dataclass


@dataclass
class SolicitudPago:
    ruta_id: int
    medio: str
    tipo_tarjeta: str | None = None

    def validar(self):
        """Comprueba los campos que vienen de la pantalla."""
        if self.ruta_id <= 0:
            raise ValueError("El identificador de ruta debe ser positivo.")
        if self.medio not in ("efectivo", "tarjeta"):
            raise ValueError("El medio debe ser efectivo o tarjeta.")
        if self.medio == "tarjeta" and self.tipo_tarjeta not in ("debito", "credito"):
            raise ValueError("Indica si la tarjeta es debito o credito.")


@dataclass
class Pago:
    id: int
    pasajero: str
    ruta: str
    monto: int
    medio: str


@dataclass
class Viaje:
    id: int
    pasajero: str
    ruta: str
    pago_id: int


class DatosRutas:
    """Entrega al servicio la ruta y tarifa que necesita consultar."""

    def __init__(self):
        self.rutas = {1: ("Ruta Norte", 3300), 2: ("Ruta Centro", 3400)}

    def buscar_ruta(self, ruta_id):
        print("DatosRutas: buscando ruta y tarifa")
        return self.rutas.get(ruta_id)


class ServicioPago:
    """Valida la solicitud y registra el pago y el viaje."""

    def __init__(self, datos):
        self.datos = datos
        self.pagos = []
        self.viajes = []

    def registrar(self, nombre_pasajero, solicitud):
        print("ServicioPago: validando los datos")
        ruta = self.datos.buscar_ruta(solicitud.ruta_id)
        if ruta is None:
            raise ValueError("La ruta no existe.")

        nombre_ruta, tarifa = ruta
        pago = Pago(len(self.pagos) + 1, nombre_pasajero, nombre_ruta, tarifa, solicitud.medio)
        viaje = Viaje(len(self.viajes) + 1, nombre_pasajero, nombre_ruta, pago.id)
        self.pagos.append(pago)
        self.viajes.append(viaje)
        print("ServicioPago: pago y viaje registrados")
        return pago, viaje


class ControladorPasajero:
    """Recibe la solicitud y llama al servicio correspondiente."""

    def __init__(self, servicio):
        self.servicio = servicio

    def pagar(self, nombre_pasajero, solicitud):
        print("ControladorPasajero: recibio la solicitud")
        solicitud.validar()
        print("SolicitudPago: campos correctos")
        return self.servicio.registrar(nombre_pasajero, solicitud)


def ejecutar():
    controlador = ControladorPasajero(ServicioPago(DatosRutas()))
    print("\n--- Escenario exitoso: pago en efectivo ---")
    pago, viaje = controlador.pagar("Ana", SolicitudPago(1, "efectivo"))
    print(f"Recibo: pago {pago.id}, viaje {viaje.id}, monto ${pago.monto}")

    print("\n--- Escenario alternativo: tarjeta sin tipo ---")
    try:
        controlador.pagar("Ana", SolicitudPago(2, "tarjeta"))
    except ValueError as error:
        print(f"Solicitud rechazada: {error}")


if __name__ == "__main__":
    ejecutar()
