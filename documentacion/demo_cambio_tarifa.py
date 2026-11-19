"""Cambia una tarifa en qrpass.db para demostrar que el catalogo vive en la base.

No toca el codigo de la aplicacion: solo actualiza la fila de la tabla `fares`.
La API y la interfaz leen el valor nuevo en la siguiente consulta, sin reiniciar
el servidor.

Uso:
    python documentacion/demo_cambio_tarifa.py
    python documentacion/demo_cambio_tarifa.py --ruta 24 --valor 3500
    python documentacion/demo_cambio_tarifa.py --revertir

El respaldo del valor original se guarda en la carpeta temporal del sistema,
asi que `--revertir` restaura exactamente lo que habia antes.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
from pathlib import Path

DB_POR_DEFECTO = Path(__file__).resolve().parents[1] / "backend" / "qrpass.db"
RESPALDO = Path(tempfile.gettempdir()) / "qrpass_demo_tarifa.json"


def buscar_tarifa(conexion: sqlite3.Connection, ruta: str, tipo_dia: str, destino: str | None):
    fila = conexion.execute(
        """
        select f.id, r.id, r.name, f.day_type, f.destination, f.amount
        from fares f
        join routes r on r.id = f.route_id
        where r.name = ? and f.day_type = ? and f.destination is ?
        """,
        (ruta, tipo_dia, destino),
    ).fetchone()
    if fila is None:
        raise SystemExit(
            f"No existe una tarifa para la ruta {ruta}, tipo {tipo_dia}, "
            f"destino {destino or 'ordinario'}."
        )
    return fila


def mostrar(fila) -> None:
    _, route_id, route_name, tipo_dia, destino, valor = fila
    print(f"  fila {fila[0]}: ruta {route_name} (id {route_id}) | {tipo_dia} | "
          f"{destino or 'sin destino'} | ${valor:,}".replace(",", "."))


def leer_respaldo() -> dict | None:
    if not RESPALDO.exists():
        return None
    return json.loads(RESPALDO.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Demostracion de tarifas leidas desde qrpass.db")
    parser.add_argument("--db", type=Path, default=DB_POR_DEFECTO, help="Ruta de qrpass.db")
    parser.add_argument("--ruta", default="24", help="Nombre de la ruta (por ejemplo 24)")
    parser.add_argument("--tipo-dia", default="weekday", choices=("weekday", "weekend"))
    parser.add_argument("--destino", default=None, help="Destino con tarifa propia; omitelo para la ordinaria")
    parser.add_argument("--valor", type=int, help="Nuevo valor en pesos")
    parser.add_argument("--revertir", action="store_true", help="Restaura el valor guardado antes del cambio")
    args = parser.parse_args()

    if not args.db.exists():
        raise SystemExit(f"No se encontro la base de datos: {args.db}")

    conexion = sqlite3.connect(args.db)
    fila = buscar_tarifa(conexion, args.ruta, args.tipo_dia, args.destino)
    fila_id, valor_actual = fila[0], fila[5]

    if args.revertir:
        respaldo = leer_respaldo()
        if respaldo is None:
            raise SystemExit("No hay un cambio pendiente por revertir.")
        if respaldo["fila_id"] != fila_id:
            raise SystemExit(
                f"El respaldo pertenece a la fila {respaldo['fila_id']}, no a la fila {fila_id}. "
                "Vuelve a indicar la misma ruta, tipo de dia y destino."
            )
        conexion.execute("update fares set amount = ? where id = ?", (respaldo["valor"], fila_id))
        conexion.commit()
        RESPALDO.unlink()
        print(f"Tarifa restaurada a ${respaldo['valor']:,}".replace(",", "."))
    elif args.valor is not None:
        if args.valor <= 0:
            raise SystemExit("El valor debe ser mayor que cero.")
        if leer_respaldo() is None:
            RESPALDO.write_text(
                json.dumps({"fila_id": fila_id, "valor": valor_actual}),
                encoding="utf-8",
            )
        conexion.execute("update fares set amount = ? where id = ?", (args.valor, fila_id))
        conexion.commit()
        print(f"Tarifa actualizada: ${valor_actual:,} -> ${args.valor:,}".replace(",", "."))
        print("Para dejarla como estaba: python documentacion/demo_cambio_tarifa.py --revertir")
    else:
        print("Tarifa actual (sin cambios):")
        mostrar(fila)
        respaldo = leer_respaldo()
        if respaldo is not None:
            print(f"  Hay un cambio pendiente de revertir: fila {respaldo['fila_id']} "
                  f"volveria a ${respaldo['valor']:,}".replace(",", "."))
        conexion.close()
        return 0

    print("Ahora en la base:")
    mostrar(buscar_tarifa(conexion, args.ruta, args.tipo_dia, args.destino))
    conexion.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
