from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MaintenanceStatusCabModel(Base):
    __tablename__ = "maintenance_status_cab"
    maintenance_status_cab_id = Column(Integer, primary_key=True)
    equipment_id = Column(Integer, nullable=False)
    maintenance_status_id = Column(Integer, nullable=False)
    active = Column(Integer, server_default=str(1))
    created_at = Column(DateTime, default=current_timestamp())
    updated_at = Column(
        DateTime, default=current_timestamp(), onupdate=current_timestamp()
    )

    def __init__(self, **kwargs):
        self.equipment_id = kwargs.get("equipment_id")
        self.maintenance_status_id = kwargs.get("maintenance_status_id")
