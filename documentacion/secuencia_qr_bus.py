"""Implementacion independiente de la secuencia para escanear el QR del bus.

El bus presenta el codigo y el pasajero lo escanea. Es una simulacion educativa:
no implementa firma criptografica, HTTP ni conexion a base de datos.
"""

from dataclasses import dataclass


@dataclass
class SolicitudQr:
    codigo: str
    clave_reintento: str


@dataclass
class Pasajero:
    nombre: str
    saldo: int


@dataclass
class Bus:
    ruta: str
    codigo_qr: str
    turno_activo: bool = True
    firma_valida: bool = True
    qr_vigente: bool = True


class Repositorio:
    """Guarda los pagos y viajes en memoria para esta demostracion."""

    def __init__(self):
        self.pagos = []
        self.viajes = []

    def guardar_abordaje(self, pasajero, ruta, monto):
        pago = {"pasajero": pasajero.nombre, "ruta": ruta, "monto": monto}
        viaje = {"pasajero": pasajero.nombre, "ruta": ruta}
        self.pagos.append(pago)
        self.viajes.append(viaje)
        print("Repositorio: pago y viaje guardados")
        return pago, viaje


class ServicioAbordaje:
    """Valida el QR y el turno, cobra el saldo y registra el abordaje."""

    def __init__(self, bus, repositorio):
        self.bus = bus
        self.repositorio = repositorio
        self.tarifas = {"Ruta Norte": 3300, "Ruta Centro": 3400}

    def validar_y_pagar(self, pasajero, solicitud):
        print("ServicioAbordaje: validando el QR y el turno")
        if solicitud.codigo != self.bus.codigo_qr:
            raise ValueError("El codigo no corresponde al QR del bus.")
        if not self.bus.firma_valida or not self.bus.qr_vigente:
            raise ValueError("El QR no tiene firma valida o esta vencido.")
        if not self.bus.turno_activo:
            raise ValueError("El turno del bus no esta activo.")
        if self.bus.ruta not in self.tarifas:
            raise ValueError("La ruta del bus no tiene una tarifa disponible.")

        monto = self.tarifas[self.bus.ruta]
        if pasajero.saldo < monto:
            raise ValueError("El saldo del pasajero es insuficiente.")

        pasajero.saldo -= monto
        print(f"ServicioAbordaje: saldo descontado, saldo actual ${pasajero.saldo}")
        return self.repositorio.guardar_abordaje(pasajero, self.bus.ruta, monto)


class ControladorPasajero:
    """Recibe los datos que la aplicacion obtiene al escanear el QR."""

    def __init__(self, servicio):
        self.servicio = servicio

    def escanear_qr(self, pasajero, solicitud):
        print("ControladorPasajero: recibio el QR escaneado")
        if not solicitud.codigo or len(solicitud.clave_reintento) < 8:
            raise ValueError("El QR o la clave de reintento no tienen formato valido.")
        return self.servicio.validar_y_pagar(pasajero, solicitud)


def ejecutar():
    pasajero = Pasajero("Ana", saldo=10000)
    bus = Bus("Ruta Norte", "QR-RUTA-NORTE-001")
    controlador = ControladorPasajero(ServicioAbordaje(bus, Repositorio()))

    print("El bus muestra su QR; el pasajero lo escanea.")
    print("\n--- Escenario exitoso ---")
    pago, viaje = controlador.escanear_qr(pasajero, SolicitudQr(bus.codigo_qr, "reintento-01"))
    print(f"Abordaje registrado en {viaje['ruta']}: ${pago['monto']}")

    print("\n--- Escenario alternativo: QR alterado ---")
    try:
        controlador.escanear_qr(pasajero, SolicitudQr("QR-INCORRECTO", "reintento-02"))
    except ValueError as error:
        print(f"Abordaje rechazado: {error}")


if __name__ == "__main__":
    ejecutar()
