from swagger_server.models.db import Base
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Sequence,
    String,
    Text,
    Time,
    ForeignKey,
    func
)


class AcessControlMaterials(Base):
    __tablename__ = 'access_control_materials'
    __table_args__ = {'schema': 'public'}

    id_material_control = Column(
        Integer,
        primary_key=True,
        nullable=False
    )

    access_control_id = Column(
        Integer,
        ForeignKey('public.biomar_access_control.id_access_control', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    material_id = Column(
        Integer,
        ForeignKey('public.biomar_materials_access.id_material', onupdate='NO ACTION', ondelete='NO ACTION'),
    )


    quantity = Column(Integer)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )