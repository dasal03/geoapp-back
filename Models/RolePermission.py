from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class RolePermissionModel(Base):
    __tablename__ = "role_permissions"

    role_permission_id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, nullable=False, index=True)
    permission_id = Column(Integer, nullable=False, index=True)
    active = Column(Integer, server_default="1", index=True)

    def __init__(self, **kwargs):
        self.role_id = kwargs.get("role_id")
        self.permission_id = kwargs.get("permission_id")
