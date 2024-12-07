from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class RoleModel(Base):
    __tablename__ = "roles"
    role_id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255), nullable=False)
    active = Column(Integer, server_default=str(1))

    def __init__(self, **kwargs):
        self.description = kwargs.get("description")
