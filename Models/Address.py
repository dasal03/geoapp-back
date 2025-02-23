from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AddressModel(Base):
    __tablename__ = "addresses"

    address_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    state = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    address = Column(String(100), nullable=False)
    apartment = Column(String(100), nullable=False)
    postcode = Column(String(100), nullable=False)
    description = Column(String(100), nullable=False)
    is_principal = Column(
        Integer, nullable=False, server_default="0", index=True
    )
    active = Column(Integer, server_default="1", index=True)

    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")
        self.state = kwargs.get("state")
        self.city = kwargs.get("city")
        self.address = kwargs.get("address")
        self.apartment = kwargs.get("apartment")
        self.postcode = kwargs.get("postcode")
        self.description = kwargs.get("description")
        self.is_principal = kwargs.get("is_principal")
