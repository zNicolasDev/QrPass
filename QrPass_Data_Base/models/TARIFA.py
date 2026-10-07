class TARIFA:
    def __init__(self, tarifa_id: int, ruta_id: int, tipo_dia: int, valor: float):
        self._tarifa_id = tarifa_id
        self._ruta_id = ruta_id
        self._tipo_dia = tipo_dia
        self._valor = valor

    @property
    def tarifa_id(self) -> int:
        return self._tarifa_id
    @tarifa_id.setter
    def tarifa_id(self, valor: int):
        self._tarifa_id = valor

    @property
    def ruta_id(self) -> int:
        return self._ruta_id
    @ruta_id.setter
    def ruta_id(self, valor: int):
        self._ruta_id = valor

    @property
    def tipo_dia(self) -> int:
        return self._tipo_dia
    @tipo_dia.setter
    def tipo_dia(self, valor: int):
        self._tipo_dia = valor

    @property
    def valor(self) -> float:
        return self._valor
    @valor.setter
    def valor(self, valor: float):
        self._valor = valor
