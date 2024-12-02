from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CountryModel(Base):
    __tablename__ = "countries"
    country_id = Column(Integer, primary_key=True, index=True)
    country_name = Column(String(255), nullable=False)
    indicative_code = Column(String(255), nullable=False)
    active = Column(Integer, server_default=str(1))

    def __init__(self, **kwargs):
        self.country_name = kwargs.get("country_name")
        self.indicative_code = kwargs.get("indicative_code")
