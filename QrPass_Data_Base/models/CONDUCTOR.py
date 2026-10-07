class CONDUCTOR:
    def __init__(self, usuario_id: int, licencia: str):
        self._usuario_id = usuario_id
        self._licencia = licencia


    @property
    def usuario_id(self) -> int: #get de usuario_id
        return self._usuario_id
    @usuario_id.setter
    def usuario_id(self, valor: int): #set de usuario_id
        self._usuario_id = valor


    @property
    def licencia(self) -> str: #get de licencia
        return self._licencia
    @licencia.setter
    def licencia(self, valor: str): #set de licencia
        self._licencia = valor

