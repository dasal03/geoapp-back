from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AccountTypeModel(Base):
    __tablename__ = "account_types"

    account_type_id = Column(Integer, primary_key=True, index=True)
    account_type = Column(String(100), nullable=False)
    active = Column(Integer, server_default="1", index=True)

    def __init__(self, **kwargs):
        self.account_type = kwargs.get("account_type")
