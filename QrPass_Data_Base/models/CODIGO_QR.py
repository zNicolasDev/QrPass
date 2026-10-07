class CODIGO_QR:
    def __init__(self, qr_id: int, usuario_id: int, token: str, estado: str):
        self._qr_id = qr_id  # Atributo interno protegido
        self._usuario_id = usuario_id
        self._token = token
        self._estado = estado



    @property
    def qr_id(self) -> int: #get de qr_id
        return self._qr_id
    @qr_id.setter
    def qr_id(self, valor: int): #set de qr_id
        self._qr_id = valor 


    @property
    def usuario_id(self) -> int: #get de usuario_id
        return self._usuario_id
    @usuario_id.setter
    def usuario_id(self, valor: int): #set de usuario_id
        self._usuario_id = valor 


    @property
    def token(self) -> str: #get de token
        return self._token
    @token.setter
    def token(self, valor: str): #set de token
        self._token = valor 


    @property
    def estado(self) -> str:
        return self._estado
    @estado.setter
    def estado(self, valor: str):
        self._estado = valor



