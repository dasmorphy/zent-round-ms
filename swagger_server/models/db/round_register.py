from swagger_server.models.db import Base
from sqlalchemy import (
    Boolean,
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


class RoundRegister(Base):
    __tablename__ = 'round_register'
    __table_args__ = {'schema': 'public'}

    id_round_register = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    round_id = Column(
        Integer,
        ForeignKey('public.rounds.id_round', onupdate='NO ACTION', ondelete='NO ACTION'),
    )

    out_round = Column(Boolean)
    observations = Column(DateTime)

    lat = Column(Text)
    long = Column(Text)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )
    created_by = Column(Text)


    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

