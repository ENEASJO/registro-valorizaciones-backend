from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Index
from app.core.database import Base

class UbicacionDB(Base):
    __tablename__ = "ubicaciones"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    tipo = Column(String(50), nullable=False)  # 'CENTRO_POBLADO' | 'CASERIO'

    # Geografía fija
    departamento = Column(String(100), nullable=False, default="Áncash")
    provincia = Column(String(100), nullable=False, default="Huari")
    distrito = Column(String(100), nullable=False, default="San Marcos")

    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ux_ubicaciones_nombre", nombre, unique=True),
    )