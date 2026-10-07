from datetime import datetime

class PAGO:
    def __init__(self, pago_id: int, usuario_id: int, tarjeta_id: int, qr_id: int, metodo: str, tipo_movimiento: str, monto: float, monto_antes: float, monto_actual: float, estado: str, fecha: datetime):
        self.pago_id = pago_id
        self.usuario_id = usuario_id
        self.tarjeta_id = tarjeta_id
        self.qr_id = qr_id
        self.metodo = metodo
        self.tipo_movimiento = tipo_movimiento
        self.monto = monto
        self.monto_antes = monto_antes
        self.monto_actual = monto_actual
        self.estado = estado
        self.fecha = fecha
 

    @property
    def pago_id(self) -> int: #get de pago_id
        return self._pago_id
    @pago_id.setter
    def pago_id(self, valor: int): #set de pago_id
        self._pago_id = valor
        
    @property
    def usuario_id(self) -> int: #get de usuario_id
        return self._usuario_id
    @usuario_id.setter
    def usuario_id(self, valor: int): #set de usuario_id
        self._usuario_id = valor    
        
    @property
    def tarjeta_id(self) -> int: #get de tarjeta_id
        return self._tarjeta_id
    @tarjeta_id.setter
    def tarjeta_id(self, valor: int): #set de tarjeta_id
        self._tarjeta_id = valor
        
    @property
    def qr_id(self) -> int: #get de qr_id
        return self._qr_id
    @qr_id.setter
    def qr_id(self, valor: int): #set de qr_id
        self._qr_id = valor
        
    @property
    def metodo(self) -> str: #get de metodo
        return self._metodo
    
    @metodo.setter
    def metodo(self, valor: str): #set de metodo
        self._metodo = valor
        
    @property
    def tipo_movimiento(self) -> str: #get de tipo_movimiento
        return self._tipo_movimiento
    @tipo_movimiento.setter
    def tipo_movimiento(self, valor: str): #set de tipo_movimiento
        self._tipo_movimiento = valor
        
    @property
    def monto(self) -> float: #get de monto
        return self._monto
    @monto.setter
    def monto(self, valor: float): #set de monto
        self._monto = valor
        
    @property
    def monto_antes(self) -> float: #get de monto_antes
        return self._monto_antes
    @monto_antes.setter
    def monto_antes(self, valor: float): #set de monto_antes
        self._monto_antes = valor
        
    @property
    def monto_actual(self) -> float: #get de monto_actual
        return self._monto_actual
    @monto_actual.setter
    def monto_actual(self, valor: float): #set de monto_actual
        self._monto_actual = valor
        
    @property
    def estado(self) -> str: #get de estado
        return self._estado
    @estado.setter
    def estado(self, valor: str): #set de estado
        self._estado = valor
        
    @property
    def fecha(self) -> datetime: #get de fecha
        return self._fecha
    @fecha.setter
    def fecha(self, valor: datetime): #set de fecha
        self._fecha = valor
        