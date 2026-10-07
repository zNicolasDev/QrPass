from datetime import datetime

class TURNO:
    def __init__(self, turno_id: int, conductor_id: int, vehiculo_id: int, ruta_id: int, inicio: datetime, fin: datetime):
        self._turno_id = turno_id
        self._conductor_id = conductor_id
        self._vehiculo_id = vehiculo_id
        self._ruta_id = ruta_id
        self._inicio = inicio
        self._fin = fin

    @property
    def turno_id(self) -> int: #get de turno_id
        return self._turno_id
    @turno_id.setter
    def turno_id(self, valor: int): #set de turno_id
        self._turno_id = valor
        
    @property
    def conductor_id(self) -> int: #get de conductor_id
        return self._conductor_id
    @conductor_id.setter
    def conductor_id(self, valor: int): #set de conductor_id
        self._conductor_id = valor
        
    @property
    def vehiculo_id(self) -> int: #get de vehiculo_id
        return self._vehiculo_id
    @vehiculo_id.setter
    def vehiculo_id(self, valor: int): #set de vehiculo_id
        self._vehiculo_id = valor
        
    @property
    def ruta_id(self) -> int: #get de ruta_id
        return self._ruta_id
    @ruta_id.setter
    def ruta_id(self, valor: int): #set de ruta_id
        self._ruta_id = valor
        
    @property
    def inicio(self) -> datetime: #get de inicio
        return self._inicio
    @inicio.setter
    def inicio(self, valor: datetime): #set de inicio
        self._inicio = valor
        
    @property
    def fin(self) -> datetime: #get de fin
        return self._fin
    @fin.setter
    def fin(self, valor: datetime): #set de fin
        self._fin = valor
