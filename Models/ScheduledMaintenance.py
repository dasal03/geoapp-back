from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ScheduledMaintenanceModel(Base):
    __tablename__ = "scheduled_maintenances"
    scheduled_maintenance_id = Column(Integer, primary_key=True)
    equipment_id = Column(Integer, nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    active = Column(Integer, server_default=str(1))

    def __init__(self, **kwargs):
        self.equipment_id = kwargs.get("equipment_id")
        self.scheduled_date = kwargs.get("scheduled_date")
