from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AddressModel(Base):
    __tablename__ = "addresses"
    address_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    country_id = Column(Integer, nullable=False)
    state_id = Column(Integer, nullable=False)
    city_id = Column(Integer, nullable=False)
    address = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    active = Column(Integer, server_default=str(1))

    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")
        self.country_id = kwargs.get("country_id")
        self.state_id = kwargs.get("state_id")
        self.city_id = kwargs.get("city_id")
        self.address = kwargs.get("address")
        self.description = kwargs.get("description")
