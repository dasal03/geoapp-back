from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MaintenanceStatusModel(Base):
    __tablename__ = "maintenance_statuses"
    maintenance_status_id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255), nullable=False)
    active = Column(Integer, server_default=str(1))
    created_at = Column(DateTime, default=current_timestamp())
    updated_at = Column(
        DateTime, default=current_timestamp(), onupdate=current_timestamp()
    )

    def __init__(self, **kwargs):
        self.description = kwargs.get("description")
