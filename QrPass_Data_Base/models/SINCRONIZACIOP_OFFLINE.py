from datetime import datetime

class SINCRONIZACIOP_OFFLINE:
    def __init__(self, sync_id: int, dispositivo_id: int, fecha_sync: datetime):
        self._sync_id = sync_id
        self._dispositivo_id = dispositivo_id
        self._fecha_sync = fecha_sync

    @property
    def sync_id(self) -> int: #get de sync_id
        return self._sync_id
    @sync_id.setter
    def sync_id(self, valor: int): #set de sync_id
        self._sync_id = valor
        
    @property
    def dispositivo_id(self) -> int: #get de dispositivo_id
        return self._dispositivo_id
    @dispositivo_id.setter
    def dispositivo_id(self, valor: int): #set de dispositivo_id
        self._dispositivo_id = valor
        
    @property
    def fecha_sync(self) -> datetime: #get de fecha_sync
        return self._fecha_sync
    @fecha_sync.setter
    def fecha_sync(self, valor: datetime): #set de fecha_sync
        self._fecha_sync = valor
