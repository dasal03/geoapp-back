from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AccountTypeModel(Base):
    __tablename__ = "account_types"
    account_type_id = Column(Integer, primary_key=True, index=True)
    account_type = Column(String(255), nullable=False)
    bank_id = Column(Integer, nullable=False)
    active = Column(Integer, server_default=str(1))

    def __init__(self, **kwargs):
        self.account_type = kwargs.get("account_type")
        self.bank_id = kwargs.get("bank_id")
