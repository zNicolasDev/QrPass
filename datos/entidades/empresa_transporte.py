class EMPRESA_TRANSPORTE:
    def __init__(self, empresa_id: int, nombre: str):
        self._empresa_id = empresa_id  # Atributo interno protegido
        self._nombre = nombre  # Atributo interno protegido

    @property
    def empresa_id(self) -> int: #get de empresa_id
        return self._empresa_id
    @empresa_id.setter
    def empresa_id(self, valor: int): #set de empresa_id
        self._empresa_id = valor


    @property
    def nombre(self) -> str: #get de nombre
        return self._nombre
    @nombre.setter
    def nombre(self, valor: str): #set de nombre
        self._nombre = valor
        
    