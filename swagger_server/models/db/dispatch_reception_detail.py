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

class DispatchReceptionDetail(Base):
    __tablename__ = 'dispatch_reception_detail'
    __table_args__ = {'schema': 'public'}

    id_reception_detail = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    reception_id = Column(
        Integer,
        ForeignKey('public.dispatch_reception.id_reception', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    product_sku_id = Column(
        Integer,
        ForeignKey('public.products_sku.id_product_sku', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    expected_quantity = Column(Integer)
    received_quantity = Column(Integer)

    observations = Column(Text)
    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

