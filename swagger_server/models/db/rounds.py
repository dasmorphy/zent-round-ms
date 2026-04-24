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


class Rounds(Base):
    __tablename__ = 'rounds'
    __table_args__ = {'schema': 'public'}

    id_round = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    start_time = Column(DateTime)
    end_time = Column(DateTime)

    status = Column(Text)

    assigned_to = Column(Text)
    assigned_by = Column(Text)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )
    created_by = Column(Text)


    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

