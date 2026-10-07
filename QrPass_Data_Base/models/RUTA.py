class RUTA:
    def __init__(self, ruta_id: int, nombre: str):
        self._ruta_id = ruta_id  # Atributo interno protegido
        self._nombre = nombre  # Atributo interno protegido
    
    @property
    def ruta_id(self) -> int: #get de ruta_id
        return self._ruta_id
    @ruta_id.setter
    def ruta_id(self, valor: int): #set de ruta_id
        self._ruta_id = valor
    
    @property
    def nombre(self) -> str: #get de nombre
        return self._nombre
    @nombre.setter
    def nombre(self, valor: str): #set de nombre
        self._nombre = valor