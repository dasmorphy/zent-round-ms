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


class ProductsSku(Base):
    __tablename__ = 'products_sku'
    __table_args__ = {'schema': 'public'}

    id_product_sku = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    product_id = Column(
        Integer,
        ForeignKey('public.dispatch_products.id_product', onupdate='NO ACTION', ondelete='NO ACTION'),
        nullable=False
    )

    sku_id = Column(
        Integer,
        ForeignKey('public.dispatch_skus.id_sku', onupdate='NO ACTION', ondelete='NO ACTION'),
        nullable=False
    )

    quantity = Column(Integer)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )


    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

