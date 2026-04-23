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


class BiomarAccessControl(Base):
    __tablename__ = 'biomar_access_control'
    __table_args__ = {'schema': 'public'}

    id_access_control = Column(
        Integer,
        primary_key=True,
        nullable=False
    )

    dni = Column(Text)
    names_visit = Column(Text)
    reason_visit = Column(Text)

    area_visit_id = Column(
        Integer,
        ForeignKey('public.area_visit.id_area', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    staff_charge_id = Column(
        Integer,
        ForeignKey('public.staff_charge.id_staff', onupdate='NO ACTION', ondelete='NO ACTION'),
    )


    observations_entry = Column(Text)
    observations_out = Column(Text)

    status = Column(Text)

    created_by = Column(Text)
    updated_by = Column(Text)
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )