from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BankAccountModel(Base):
    __tablename__ = "bank_accounts"
    bank_account_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    bank_id = Column(Integer, nullable=False)
    account_type_id = Column(Integer, nullable=False)
    account_number = Column(String(255), nullable=False)
    principal_account = Column(Integer, nullable=False)
    active = Column(Integer, server_default=str(1))

    def __init__(self, **kwargs):
        self.bank_id = kwargs.get("bank_id")
        self.user_id = kwargs.get("user_id")
        self.account_type_id = kwargs.get("account_type_id")
        self.account_number = kwargs.get("account_number")
        self.principal_account = kwargs.get("principal_account")
