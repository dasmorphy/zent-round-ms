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


class StaffCharge(Base):
    __tablename__ = 'staff_charge'
    __table_args__ = {'schema': 'public'}

    id_staff = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name = Column(Text)


    created_at = Column(
        DateTime,
        server_default=func.now()
    )


    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

