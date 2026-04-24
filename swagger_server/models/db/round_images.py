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


class RoundImages(Base):
    __tablename__ = 'round_images'
    __table_args__ = {'schema': 'public'}

    id_image = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    round_id = Column(
        Integer,
        ForeignKey('public.round_register.id_round_register', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    image_path = Column(Text)

    
    created_at = Column(
        DateTime,
        server_default=func.now()
    )


    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

