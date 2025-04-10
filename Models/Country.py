from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CountryModel(Base):
    __tablename__ = "countries"

    country_id = Column(Integer, primary_key=True, index=True)
    country_name = Column(String(100), nullable=False)
    active = Column(Integer, server_default="1", index=True)

    def __init__(self, **kwargs):
        self.country_id = kwargs.get("country_id")
        self.country_name = kwargs.get("country_name")
