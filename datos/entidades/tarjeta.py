class TARJETA:
    def __init__(self, tarjeta_id: int, usuario_id: int, nombre_banco: str, tipo: str):
        self._tarjeta_id = tarjeta_id
        self._usuario_id = usuario_id
        self._nombre_banco = nombre_banco
        self._tipo = tipo

    @property
    def tarjeta_id(self) -> int:
        return self._tarjeta_id
    @tarjeta_id.setter
    def tarjeta_id(self, valor: int):
        self._tarjeta_id = valor

    @property
    def usuario_id(self) -> int:
        return self._usuario_id
    @usuario_id.setter
    def usuario_id(self, valor: int):
        self._usuario_id = valor

    @property
    def nombre_banco(self) -> str:
        return self._nombre_banco
    @nombre_banco.setter
    def nombre_banco(self, valor: str):
        self._nombre_banco = valor

    @property
    def tipo(self) -> str:
        return self._tipo
    @tipo.setter
    def tipo(self, valor: str):
        self._tipo = valor
