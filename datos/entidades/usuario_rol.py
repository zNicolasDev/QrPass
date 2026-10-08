class USUARIO_ROL:
    def __init__(self, usuario_id: int, rol_id: int):
         self._usuario_id = usuario_id  # Atributo interno protegido
         self._rol_id = rol_id  # Atributo interno protegido

    @property
    def usuario_id(self) -> int:
        return self._usuario_id
    @usuario_id.setter
    def usuario_id(self, valor: int):
        self._usuario_id = valor

    @property
    def rol_id(self) -> int:
        return self._rol_id
    @rol_id.setter
    def rol_id(self, valor: int):
        self._rol_id = valor