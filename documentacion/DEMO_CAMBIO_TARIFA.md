# Demo: cambiar una tarifa en la base de datos

Objetivo: demostrar en 1 minuto que **ninguna tarifa está escrita en el código**.
El valor que cobra la API sale de la tabla `fares` de `qrpass.db`.

> La base de entrega no se modifica en esta guía. Los comandos se ejecutan sobre
> `backend/qrpass.db`, que es la base que usa `iniciar.bat`.

## Antes de empezar

1. Ejecuta `iniciar.bat` desde la raíz del proyecto. Se abre
   `http://127.0.0.1:8000`.
2. Entra con `conductor@qrpass.com` / `Clave-Segura-2026` y deja abierta la
   pantalla del conductor.
3. Consulta el valor inicial (ruta 24, día hábil):

```powershell
python documentacion/demo_cambio_tarifa.py
```

Debe mostrar la fila 33 con `$3.300`. La misma consulta en la API:

```text
http://127.0.0.1:8000/api/v1/fares/current?route_id=17
```

## Paso 1: cambiar el valor solo en la BD

```powershell
python documentacion/demo_cambio_tarifa.py --ruta 24 --valor 3500
```

No se tocó ningún archivo `.py`, ni se reinició el servidor. El script guarda
el valor original en la carpeta temporal para poder revertirlo.

## Paso 2: mostrar que la aplicación ya lo usa

- Vuelve a cargar la misma dirección `/api/v1/fares/current?route_id=17`:
  `"amount": 3500`.
- Recarga la pantalla del conductor: el pago manual dice **+ $ 3.500**.
- Si se inicia un turno y se paga escaneando el QR, el comprobante dice
  **$ 3.500** y el saldo se descuenta por ese valor.

Es decir: la tarifa la leyó la API desde la base, no desde una constante.

## Paso 3: dejar todo como estaba

```powershell
python documentacion/demo_cambio_tarifa.py --revertir
python documentacion/demo_cambio_tarifa.py
```

La última consulta debe volver a mostrar `$3.300`.

## Cómo explicarlo en 30 segundos

> `app_config` es el recetario y la tabla `fares` son los platos ya servidos.
> Cambiamos el plato directamente en la nevera (la base), sin tocar la cocina
> (el código). La API fue a la nevera y nos cobró el valor nuevo. Al terminar
> devolvimos el plato a su valor original.

## Notas

- `iniciar.bat` ejecuta `import-catalog` cada vez que arranca y reaplica el
  catálogo maestro guardado en `app_config`; por eso la demo se hace sin
  reiniciar y se revierte al final.
- Si se quiere ver otro valor, cambia `--valor 3500` por el que se necesite.
- Para ver o editar la fila a mano con un explorador SQLite:

```sql
select f.id, r.name, f.day_type, f.destination, f.amount
from fares f
join routes r on r.id = f.route_id
where r.name = '24';

-- Solo si se va a usar el id que muestra la consulta anterior:
update fares set amount = 3500 where id = 33;
```
