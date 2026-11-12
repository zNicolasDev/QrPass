from __future__ import annotations

import argparse
import getpass
import sys

from sqlalchemy import func, select

from app.core.database import BaseDatos
from app.models import Conductor, Pago, Ruta, Tarifa, Turno, Usuario, Viaje
from app.servicios.catalogo import importar_catalogo
from app.servicios.turnos import asignar_turno_conductor
from app.servicios.usuarios import crear_administrador, crear_conductor


def _leer_contrasena(value: str | None) -> str:
    if value:
        if len(value) < 12:
            raise SystemExit("La contraseña debe tener al menos 12 caracteres.")
        return value
    password = getpass.getpass("Contraseña (mínimo 12 caracteres): ")
    if len(password) < 12:
        raise SystemExit("La contraseña debe tener al menos 12 caracteres.")
    confirmation = getpass.getpass("Repite la contraseña: ")
    if password != confirmation:
        raise SystemExit("Las contraseñas no coinciden.")
    return password


def _abrir_base() -> BaseDatos:
    database = BaseDatos()
    database.initialize()
    return database


def comando_init(_: argparse.Namespace) -> None:
    database = _abrir_base()
    database.close()
    print("Base de datos preparada con el esquema y los roles del sistema.")


def comando_importar_catalogo(_: argparse.Namespace) -> None:
    database = _abrir_base()
    try:
        with database.session_factory() as session:
            resumen = importar_catalogo(session)
    finally:
        database.close()
    print(
        "Catálogo importado: "
        f"{resumen['rutas_creadas']} rutas nuevas, "
        f"{resumen['rutas_actualizadas']} rutas actualizadas, "
        f"{resumen['tarifas_creadas']} tarifas nuevas, "
        f"{resumen['tarifas_actualizadas']} tarifas actualizadas."
    )


def comando_crear_conductor(args: argparse.Namespace) -> None:
    password = _leer_contrasena(args.contrasena)
    database = _abrir_base()
    try:
        with database.session_factory() as session:
            user = crear_conductor(
                session,
                names=args.nombre,
                email=args.correo,
                password=password,
                license_number=args.licencia,
            )
            if args.ruta:
                route = session.scalar(select(Ruta).where(Ruta.nombre == args.ruta))
                if route is None:
                    raise SystemExit(
                        f"La ruta {args.ruta!r} no existe. Ejecuta 'import-catalog' primero."
                    )
                if not args.placa:
                    raise SystemExit("Indica la placa del vehículo con --placa para asignar el turno.")
                asignar_turno_conductor(
                    session,
                    user,
                    route_id=route.id,
                    plate=args.placa,
                    company_name=args.empresa,
                )
    finally:
        database.close()
    print(f"Conductor creado: {args.correo}")
    if args.ruta:
        print(f"Turno asignado en la ruta {args.ruta} con el vehículo {args.placa.upper()}.")


def comando_asignar_ruta(args: argparse.Namespace) -> None:
    database = _abrir_base()
    try:
        with database.session_factory() as session:
            user = session.scalar(select(Usuario).where(Usuario.correo == args.correo))
            if user is None or session.get(Conductor, user.id) is None:
                raise SystemExit("No existe un conductor con ese correo.")
            route = session.scalar(select(Ruta).where(Ruta.nombre == args.ruta))
            if route is None:
                raise SystemExit(f"La ruta {args.ruta!r} no existe. Ejecuta 'import-catalog' primero.")
            if not args.placa:
                raise SystemExit("Indica la placa del vehículo con --placa.")
            asignar_turno_conductor(
                session,
                user,
                route_id=route.id,
                plate=args.placa,
                company_name=args.empresa,
            )
    finally:
        database.close()
    print(f"Ruta {args.ruta} asignada al conductor {args.correo} con el vehículo {args.placa.upper()}.")


def comando_crear_administrador(args: argparse.Namespace) -> None:
    password = _leer_contrasena(args.contrasena)
    database = _abrir_base()
    try:
        with database.session_factory() as session:
            crear_administrador(
                session,
                names=args.nombre,
                email=args.correo,
                password=password,
            )
    finally:
        database.close()
    print(f"Administrador creado: {args.correo}")


def comando_estado(_: argparse.Namespace) -> None:
    database = _abrir_base()
    try:
        with database.session_factory() as session:
            total_usuarios = session.scalar(select(func.count(Usuario.id))) or 0
            total_conductores = session.scalar(select(func.count(Conductor.usuario_id))) or 0
            total_rutas = session.scalar(select(func.count(Ruta.id))) or 0
            total_tarifas = session.scalar(select(func.count(Tarifa.id))) or 0
            turnos_abiertos = session.scalar(
                select(func.count(Turno.id)).where(Turno.finaliza_en.is_(None))
            ) or 0
            total_pagos = session.scalar(select(func.count(Pago.id))) or 0
            total_viajes = session.scalar(select(func.count(Viaje.id))) or 0
    finally:
        database.close()
    print(f"Usuarios: {total_usuarios}")
    print(f"Conductores: {total_conductores}")
    print(f"Rutas: {total_rutas}")
    print(f"Tarifas: {total_tarifas}")
    print(f"Turnos abiertos: {turnos_abiertos}")
    print(f"Pagos: {total_pagos}")
    print(f"Viajes: {total_viajes}")


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.management",
        description="Administración de la base de datos y las cuentas de QrPass.",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    init = subparsers.add_parser("init", help="Crea el esquema y los roles del sistema.")
    init.set_defaults(func=comando_init)

    catalogo = subparsers.add_parser(
        "import-catalog",
        help="Importa las rutas y tarifas del catálogo maestro.",
    )
    catalogo.set_defaults(func=comando_importar_catalogo)

    conductor = subparsers.add_parser(
        "create-driver",
        help="Crea una cuenta con roles PASSENGER y DRIVER.",
    )
    conductor.add_argument("--nombre", required=True, help="Nombre completo del conductor.")
    conductor.add_argument("--correo", required=True, help="Correo que se usará como usuario.")
    conductor.add_argument("--contrasena", help="Contraseña de al menos 12 caracteres.")
    conductor.add_argument("--licencia", required=True, help="Número de licencia de conducción.")
    conductor.add_argument("--ruta", help="Nombre de la ruta asignada, por ejemplo 24.")
    conductor.add_argument("--placa", help="Placa del vehículo asignado.")
    conductor.add_argument("--empresa", default="QrPass", help="Empresa de transporte del vehículo.")
    conductor.set_defaults(func=comando_crear_conductor)

    asignar = subparsers.add_parser(
        "assign-route",
        help="Asigna una ruta adicional a un conductor existente.",
    )
    asignar.add_argument("--correo", required=True, help="Correo del conductor.")
    asignar.add_argument("--ruta", required=True, help="Nombre de la ruta, por ejemplo 24.")
    asignar.add_argument("--placa", required=True, help="Placa del vehículo.")
    asignar.add_argument("--empresa", default="QrPass", help="Empresa de transporte del vehículo.")
    asignar.set_defaults(func=comando_asignar_ruta)

    admin = subparsers.add_parser(
        "create-admin",
        help="Crea una cuenta con roles PASSENGER y ADMIN.",
    )
    admin.add_argument("--nombre", required=True, help="Nombre completo de la persona administradora.")
    admin.add_argument("--correo", required=True, help="Correo que se usará como usuario.")
    admin.add_argument("--contrasena", help="Contraseña de al menos 12 caracteres.")
    admin.set_defaults(func=comando_crear_administrador)

    estado = subparsers.add_parser("status", help="Muestra un resumen de los datos guardados.")
    estado.set_defaults(func=comando_estado)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
