class ROL:
    def __init__(self, rol_id: int, codigo: str, nombre: str):
        self._rol_id = rol_id  # Atributo interno protegido
        self._codigo = codigo
        self._nombre = nombre


    @property
    def rol_id(self) -> int: #get de rol_id
        return self._rol_id
    @rol_id.setter
    def rol_id(self, valor: int): #set de rol_id
        self._rol_id = valor 
        
    @property
    def codigo(self) -> str: #get de codigo
        return self._codigo
    @codigo.setter
    def codigo(self, valor: str): #set de codigo    
        self._codigo = valor

    @property
    def nombre(self) -> str: #get de nombre
        return self._nombre
    @nombre.setter
    def nombre(self, valor: str): #set de nombre
        self._nombre = valor