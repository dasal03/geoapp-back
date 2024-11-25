from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class EquipmentModel(Base):
    __tablename__ = "equipments"
    equipment_id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255), nullable=False)
    location_id = Column(Integer, nullable=False)
    serial = Column(String(255), nullable=False)
    model = Column(String(255), nullable=False)
    image = Column(Text, nullable=False)
    active = Column(Integer, server_default=str(1))
    created_at = Column(DateTime, default=current_timestamp())
    updated_at = Column(
        DateTime, default=current_timestamp(), onupdate=current_timestamp()
    )

    def __init__(self, **kwargs):
        self.description = kwargs.get("description")
        self.location_id = kwargs.get("location_id")
        self.serial = kwargs.get("serial")
        self.model = kwargs.get("model")
        self.image = kwargs.get("image")
