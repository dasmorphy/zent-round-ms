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


class DispatchImages(Base):
    __tablename__ = 'dispatch_images'
    __table_args__ = {'schema': 'public'}

    id_image = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    dispatch_id = Column(
        Integer,
        ForeignKey('public.dispatch.id_dispatch', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    process = Column(Text)
    image_path = Column(Text)

    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )


    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

