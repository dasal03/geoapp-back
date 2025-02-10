import re
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PaymentCardModel(Base):
    __tablename__ = "payment_cards"

    payment_card_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    bank_id = Column(Integer, nullable=False, index=True)
    account_type_id = Column(Integer, nullable=False, index=True)
    card_number = Column(String(15), nullable=False)
    expiration_date = Column(String(5), nullable=False)
    cvv = Column(String(3), nullable=False)
    is_principal = Column(
        Integer, nullable=False, server_default="0", index=True
    )
    active = Column(Integer, server_default="1", index=True)

    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")
        self.bank_id = kwargs.get("bank_id")
        self.account_type_id = kwargs.get("account_type_id")
        self.card_number = kwargs.get("card_number")
        self.expiration_date = kwargs.get("expiration_date")
        self.cvv = kwargs.get("cvv")
        self.is_principal = kwargs.get("is_principal")

    @staticmethod
    def validate_expiration_date(expiration_date):
        """Validate expiration date format."""
        if (
            not expiration_date
            or not re.match(r"^(0[1-9]|1[0-2])\/\d{2}$", expiration_date)
        ):
            raise ValueError(
                "La fecha de expiración debe estar en el formato mm/yy."
            )
        return expiration_date
