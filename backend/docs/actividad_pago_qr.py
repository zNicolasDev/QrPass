"""Implementacion independiente de la actividad de pago con QR.

Cada condicion representa una decision del diagrama. Los datos se guardan en
memoria y el ejemplo no depende de la API de QrPass.
"""

from dataclasses import dataclass


@dataclass
class Pasajero:
    saldo: int


@dataclass
class DatosQr:
    codigo: str
    firma_valida: bool
    vigente: bool
    ruta_qr: str
    ruta_turno: str
    turno_activo: bool


class RegistroMemoria:
    """Simula el guardado conjunto del pago y el viaje."""

    def __init__(self, guardar_correctamente=True):
        self.pagos = []
        self.viajes = []
        self.guardar_correctamente = guardar_correctamente

    def guardar_pago_y_viaje(self, ruta, monto):
        if not self.guardar_correctamente:
            return False
        self.pagos.append({"ruta": ruta, "monto": monto})
        self.viajes.append({"ruta": ruta, "pago": len(self.pagos)})
        return True


def pagar_abordaje(pasajero, qr, registro):
    """Recorre las decisiones y actividades del diagrama."""
    print("Inicio: pasajero escanea el codigo")
    if not qr.codigo:
        return "Rechazado: el codigo esta vacio."
    print("Decision: el codigo tiene contenido")

    if not qr.firma_valida or not qr.vigente:
        return "Rechazado: firma incorrecta o QR vencido."
    print("Decision: firma y vigencia correctas")

    if not qr.turno_activo or not qr.ruta_qr:
        return "Rechazado: no hay turno activo o ruta valida."
    if qr.ruta_qr != qr.ruta_turno:
        return "Rechazado: la ruta del QR no coincide con la del turno."
    print("Decision: turno activo y ruta disponible")

    tarifas = {"Ruta Norte": 3300, "Ruta Centro": 3400}
    if qr.ruta_qr not in tarifas:
        return "Rechazado: no se encontro la tarifa de la ruta."

    monto = tarifas[qr.ruta_qr]
    if pasajero.saldo < monto:
        return "Rechazado: saldo insuficiente."
    print("Decision: saldo suficiente")

    saldo_anterior = pasajero.saldo
    cantidad_pagos = len(registro.pagos)
    cantidad_viajes = len(registro.viajes)
    pasajero.saldo -= monto
    print("Actividad: descontar saldo y guardar pago y viaje")

    guardado = registro.guardar_pago_y_viaje(qr.ruta_qr, monto)
    if not guardado:
        pasajero.saldo = saldo_anterior
        del registro.pagos[cantidad_pagos:]
        del registro.viajes[cantidad_viajes:]
        return "Operacion cancelada: no se guardaron los registros."

    return f"Abordaje aprobado: ${monto}. Saldo restante: ${pasajero.saldo}."


def ejecutar():
    registro = RegistroMemoria()
    pasajero = Pasajero(saldo=7000)
    qr_valido = DatosQr("QR-001", True, True, "Ruta Norte", "Ruta Norte", True)

    print("\n--- Escenario exitoso ---")
    print(pagar_abordaje(pasajero, qr_valido, registro))

    print("\n--- Escenario alternativo: saldo insuficiente ---")
    pasajero.saldo = 1000
    print(pagar_abordaje(pasajero, qr_valido, registro))

    print("\n--- Escenario alternativo: ruta del QR distinta a la del turno ---")
    qr_ruta_incorrecta = DatosQr("QR-002", True, True, "Ruta Centro", "Ruta Norte", True)
    print(pagar_abordaje(pasajero, qr_ruta_incorrecta, registro))

    print("\n--- Escenario alternativo: fallo al guardar los registros ---")
    pasajero.saldo = 5000
    registro_con_fallo = RegistroMemoria(guardar_correctamente=False)
    print(pagar_abordaje(pasajero, qr_valido, registro_con_fallo))
    print(f"Saldo despues de cancelar: ${pasajero.saldo}")


if __name__ == "__main__":
    ejecutar()
