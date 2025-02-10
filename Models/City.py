from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CityModel(Base):
    __tablename__ = "cities"

    city_id = Column(Integer, primary_key=True, index=True)
    state_id = Column(Integer, nullable=False, index=True)
    city_name = Column(String(100), nullable=False)
    active = Column(Integer, server_default="1", index=True)

    def __init__(self, **kwargs):
        self.city_name = kwargs.get("city_name")
        self.state_id = kwargs.get("state_id")
