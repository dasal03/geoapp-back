from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PermissionModel(Base):
    __tablename__ = "permissions"

    permission_id = Column(Integer, primary_key=True, index=True)
    permission_name = Column(String(255), nullable=False)
    active = Column(Integer, server_default="1", index=True)

    def __init__(self, **kwargs):
        self.permission_name = kwargs.get("permission_name")
