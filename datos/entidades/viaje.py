from datetime import datetime

class VIAJE:
    def __init__(self, viaje_id: int, pago_id: int, turno_id: int, tarifa_id: int, fecha_hora: datetime):
        self._viaje_id = viaje_id
        self._pago_id = pago_id
        self._turno_id = turno_id
        self._tarifa_id = tarifa_id
        self._fecha_hora = fecha_hora

    @property
    def viaje_id(self) -> int: #get de viaje_id
        return self._viaje_id
    @viaje_id.setter
    def viaje_id(self, valor: int): #set de viaje_id
        self._viaje_id = valor
        
    @property
    def pago_id(self) -> int: #get de pago_id
        return self._pago_id
    @pago_id.setter
    def pago_id(self, valor: int): #set de pago_id
        self._pago_id = valor
        
    @property
    def turno_id(self) -> int: #get de turno_id
        return self._turno_id
    @turno_id.setter
    def turno_id(self, valor: int): #set de turno_id
        self._turno_id = valor
        
    @property
    def tarifa_id(self) -> int: #get de tarifa_id
        return self._tarifa_id
    @tarifa_id.setter
    def tarifa_id(self, valor: int): #set de tarifa_id
        self._tarifa_id = valor
        
    @property
    def fecha_hora(self) -> datetime: #get de fecha_hora
        return self._fecha_hora
    @fecha_hora.setter
    def fecha_hora(self, valor: datetime): #set de fecha_hora
        self._fecha_hora = valor