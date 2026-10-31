# ANEXO D. EJECUCIÓN DE PRUEBAS

Desde `backend/`:

```powershell
py -m pytest -q
```

Con detalle:
```powershell
py -m pytest -v
```

Específicas:
```powershell
py -m pytest tests/test_api.py -v
py -m pytest tests/test_models_dtos.py -v
```

Las pruebas usan `TestClient` con base de datos en memoria.
