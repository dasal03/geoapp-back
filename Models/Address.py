from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AddressModel(Base):
    __tablename__ = "addresses"

    address_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    state_id = Column(Integer, nullable=False, index=True)
    city_id = Column(Integer, nullable=False, index=True)
    address = Column(String(100), nullable=False)
    is_principal = Column(
        Integer, nullable=False, server_default="0", index=True
    )
    active = Column(Integer, server_default="1", index=True)

    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")
        self.state_id = kwargs.get("state_id")
        self.city_id = kwargs.get("city_id")
        self.address = kwargs.get("address")
        self.is_principal = kwargs.get("is_principal")
