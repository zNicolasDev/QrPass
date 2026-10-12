from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # Los models heredan de esta base para que SQLAlchemy registre sus tablas
    # en Base.metadata y pueda crearlas o inspeccionarlas en conjunto.
    pass
