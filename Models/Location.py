from sqlalchemy import Column, Integer, String, Double
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class LocationModel(Base):
    __tablename__ = "locations"
    location_id = Column(Integer, primary_key=True, index=True)
    zone_name = Column(String(255), nullable=False)
    lat_min = Column(Double(), nullable=False)
    lat_max = Column(Double(), nullable=False)
    long_min = Column(Double(), nullable=False)
    long_max = Column(Double(), nullable=False)

    def __init__(self, **kwargs):
        self.zone_name = kwargs.get("zone_name")
        self.lat_min = kwargs.get("lat_min")
        self.lat_max = kwargs.get("lat_max")
        self.long_min = kwargs.get("long_min")
        self.long_max = kwargs.get("long_max")
