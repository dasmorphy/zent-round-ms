from swagger_server.models.db import Base
from sqlalchemy import (
    Boolean,
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

class DispatchReception(Base):
    __tablename__ = 'dispatch_reception'
    __table_args__ = {'schema': 'public'}

    id_reception = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    dispatch_id = Column(
        Integer,
        ForeignKey('public.dispatch.id_dispatch', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    is_correct = Column(Boolean, default=True)

    observations = Column(Text)
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    created_by = Column(Text)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

