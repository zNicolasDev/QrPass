class VEHICULO:
    def __init__(self, vehiculo_id: int, emppresa: int, placa: str):
        self._vehiculo_id = vehiculo_id  # Atributo interno protegido
        self._emppresa = emppresa
        self._placa = placa

    @property
    def vehiculo_id(self) -> int:
        return self._vehiculo_id
    @vehiculo_id.setter
    def vehiculo_id(self, valor: int):
        self._vehiculo_id = valor 

    @property
    def emppresa(self) -> int:
        return self._emppresa
    @emppresa.setter
    def emppresa(self, valor: int):
        self._emppresa = valor 

    @property
    def placa(self) -> str:
        return self._placa
    @placa.setter
    def placa(self, valor: str):
        self._placa = valor

