from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BankModel(Base):
    __tablename__ = "banks"
    bank_id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String(255), nullable=False)
    country_id = Column(Integer, nullable=False)
    active = Column(Integer, server_default=str(1))

    def __init__(self, **kwargs):
        self.bank_name = kwargs.get("bank_name")
        self.country_id = kwargs.get("country_id")
