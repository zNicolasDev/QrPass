class TRASBORDO:
    def __init__(self, trasbordo_id: int, viaje_origen_id: int, ruta_destino_id: int):
         self._trasbordo_id = trasbordo_id
         self._viaje_origen_id = viaje_origen_id
         self._ruta_destino_id = ruta_destino_id

    @property
    def trasbordo_id(self) -> int:
        return self._trasbordo_id
    @trasbordo_id.setter
    def trasbordo_id(self, valor: int):
        self._trasbordo_id = valor

    @property
    def viaje_origen_id(self) -> int:
        return self._viaje_origen_id
    @viaje_origen_id.setter
    def viaje_origen_id(self, valor: int):
        self._viaje_origen_id = valor

    @property
    def ruta_destino_id(self) -> int:
        return self._ruta_destino_id
    @ruta_destino_id.setter
    def ruta_destino_id(self, valor: int):
        self._ruta_destino_id = valor