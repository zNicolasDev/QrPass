class DISPOTIVO_ABORDO:
    def __init__(self, dispotivo_id: int, vehiculo_id: int, serial: str):
            self._dispotivo_id = dispotivo_id  # Atributo interno protegido
            self._vehiculo_id = vehiculo_id
            self._serial = serial
            
            
    @property
    def dispotivo_id(self) -> int: #get de dispotivo_id  
        return self._dispotivo_id
    @dispotivo_id.setter
    def dispotivo_id(self, valor: int): #set de dispotivo_id
        self._dispotivo_id = valor
            
            
    @property
    def vehiculo_id(self) -> int: #get de vehiculo_id
        return self._vehiculo_id
    @vehiculo_id.setter
    def vehiculo_id(self, valor: int): #set de vehiculo_id
        self._vehiculo_id = valor


    @property
    def serial(self) -> str: #get de serial
        return self._serial
    @serial.setter
    def serial(self, valor: str): #set de serial
        self._serial = valor 