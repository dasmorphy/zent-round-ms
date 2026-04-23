from swagger_server.models.db import Base
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    Time,
    ForeignKey,
    func
)


class DispatchSkus(Base):
    __tablename__ = 'dispatch_skus'
    __table_args__ = {'schema': 'public'}

    id_sku = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    dispatch_id = Column(
        Integer,
        ForeignKey('public.dispatch.id_dispatch', onupdate='NO ACTION', ondelete='NO ACTION'),
        nullable=False
    )

    type_sku = Column(Text)
    
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

