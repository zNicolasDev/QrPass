class USUARIO:
    def __init__(self, usuario_id: int, nombres: str, documentos: str, monto_billetera: float, estado: str):
        self._usuario_id = usuario_id  # Atributo interno protegido
        self._nombres = nombres  # Atributo interno protegido
        self._documentos = documentos  # Atributo interno protegido
        self._monto_billetera = monto_billetera  # Atributo interno protegido
        self._estado = estado  # Atributo interno protegido

    @property
    def usuario_id(self) -> int:
        return self._usuario_id
    @usuario_id.setter
    def usuario_id(self, valor: int):
        self._usuario_id = valor

    @property
    def nombres(self) -> str:
        return self._nombres
    @nombres.setter
    def nombres(self, valor: str):
        self._nombres = valor

    @property
    def documentos(self) -> str:
        return self._documentos
    @documentos.setter
    def documentos(self, valor: str):
        self._documentos = valor

    @property
    def monto_billetera(self) -> float:
        return self._monto_billetera
    @monto_billetera.setter
    def monto_billetera(self, valor: float):
        self._monto_billetera = valor

    @property
    def estado(self) -> str:
        return self._estado
    @estado.setter
    def estado(self, valor: str):
        self._estado = valor


