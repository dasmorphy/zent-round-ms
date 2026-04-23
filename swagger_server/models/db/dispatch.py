from swagger_server.models.db import Base
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Table,
    Text,
    Time,
    ForeignKey,
    func
)

class Dispatch(Base):
    __tablename__ = 'dispatch'
    __table_args__ = {'schema': 'public'}

    id_dispatch = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    status_id = Column(
        Integer,
        ForeignKey('public.dispatch_status.id_status', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    vehicle_type_id = Column(
        Integer,
        ForeignKey('public.vehicle_type.id_vehicle_type', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    destiny_id = Column(
        Integer,
        ForeignKey('public.destiny_intern.id_destiny', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    driver = Column(Text)
    order_number = Column(Text)
    observations = Column(Text)
    truck_license = Column(Text)
    weight = Column(Integer)

    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    created_by = Column(Text)
    updated_by = Column(Text)


    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

