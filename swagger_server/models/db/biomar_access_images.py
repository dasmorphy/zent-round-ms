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


class BiomarAccessImages(Base):
    __tablename__ = 'biomar_access_images'
    __table_args__ = {'schema': 'public'}

    id_image = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    access_control_id = Column(
        Integer,
        ForeignKey('public.biomar_access_control.id_access_control', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    type_process = Column(Text)
    image_path = Column(Text)

    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )


    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

