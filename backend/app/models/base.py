# Este archivo define la base declarativa compartida por las entidades SQLAlchemy.
from sqlalchemy.orm import DeclarativeBase


# Base compartida que conecta las clases Python con las tablas de la base de datos.
class Base(DeclarativeBase):
    # Los models heredan de esta base para que SQLAlchemy registre sus tablas
    # en Base.metadata y pueda crearlas o inspeccionarlas en conjunto.
    # En las demás entidades, Mapped indica el tipo Python de un dato,
    # mapped_column define la columna SQL y ForeignKey enlaza tablas.
    # relationship conecta objetos; back_populates nombra la relación del otro lado.
    pass
