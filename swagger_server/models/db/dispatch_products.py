from swagger_server.models.db import Base
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    ForeignKey,
    func
)


class DispatchProducts(Base):
    __tablename__ = 'dispatch_products'
    __table_args__ = {'schema': 'public'}

    id_product = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name = Column(Text)
    price = Column(Numeric)
    stock = Column(Integer)
    presentation_type = Column(Text)

    
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

