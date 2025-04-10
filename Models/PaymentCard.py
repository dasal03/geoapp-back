from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PaymentCardModel(Base):
    __tablename__ = "payment_cards"

    payment_card_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    number = Column(String(16), nullable=False)
    expiry = Column(String(5), nullable=False)
    cvc = Column(String(255), nullable=False)
    is_principal = Column(
        Integer, nullable=False, server_default="1", index=True
    )
    active = Column(Integer, server_default="1", index=True)

    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")
        self.name = kwargs.get("name")
        self.number = kwargs.get("number")
        self.expiry = kwargs.get("expiry")
        self.cvc = kwargs.get("cvc")
        self.is_principal = kwargs.get("is_principal")
