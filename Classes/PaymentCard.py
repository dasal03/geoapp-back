from typing import Any, Dict
from sqlalchemy import insert, select, update, and_
from Models.User import UserModel
from Models.Bank import BankModel
from Models.PaymentCard import PaymentCardModel
from Utils.Constants import (
    ACTIVE,
    INACTIVE,
    SUCCESS_STATUS,
    CREATED_STATUS,
    ERROR_STATUS,
    NO_DATA_STATUS,
)
from Utils.Response import _response
from Utils.Validations import Validations
from Utils.GeneralTools import get_input_data
from Utils.ExceptionsTools import CustomException


class PaymentCard:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)
        self.fields = {
            "user_id": int,
            "bank_id": int,
            "card_number": str,
            "expiration_date": str,
            "cvv": str,
        }

    def get_user_cards(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        user_id = request.get("user_id")

        self.validations.records(
            conn=self.db,
            model=UserModel,
            pk=user_id,
            error_class=CustomException(
                "No se encontró el usuario.", NO_DATA_STATUS
            ),
            as_dict=True,
        )

        stmt = (
            select(
                PaymentCardModel,
                BankModel.bank_name,
            )
            .join(
                BankModel,
                and_(
                    PaymentCardModel.bank_id == BankModel.bank_id,
                    BankModel.active == ACTIVE,
                ),
            )
            .where(
                PaymentCardModel.user_id == user_id,
                PaymentCardModel.active == ACTIVE
            )
        )
        payment_cards = self.db.query(stmt)

        return (
            _response(payment_cards.as_dict(), SUCCESS_STATUS)
            if payment_cards
            else _response(
                "No hay tarjetas vinculadas.", NO_DATA_STATUS
            )
        )

    def add_payment_card(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        user_id = request.get("user_id")
        is_principal = request.get("is_principal", 1)

        self.validations.records(
            conn=self.db,
            model=UserModel,
            pk=user_id,
            error_class=CustomException(
                "No se encontró el usuario.", NO_DATA_STATUS),
            as_dict=True,
        )

        self.validations.validate_data(request, self.fields)

        stmt = insert(PaymentCardModel).values(
            user_id=user_id,
            bank_id=request.get("bank_id"),
            card_number=request.get("card_number"),
            expiration_date=request.get("expiration_date"),
            cvv=request.get("cvv"),
            is_principal=is_principal,
        )
        payment_card_id = self.db.add(stmt)

        return (
            _response({"payment_card_id": payment_card_id}, CREATED_STATUS)
            if payment_card_id
            else _response(
                "No se pudo vincular la tarjeta.", ERROR_STATUS
            )
        )

    def update_payment_card(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        user_id = request.get("user_id")
        payment_card_id = request.get("payment_card_id")
        is_principal = request.get("is_principal")

        self.validations.records(
            conn=self.db,
            model=UserModel,
            pk=user_id,
            error_class=CustomException(
                "No se encontró el usuario.", NO_DATA_STATUS),
            as_dict=True,
        )

        self.validations.records(
            conn=self.db,
            model=PaymentCardModel,
            pk=payment_card_id,
            error_class=CustomException(
                "No hay tarjetas vinculadas.", NO_DATA_STATUS),
            as_dict=True,
        )

        update_values = {
            key: value for key, value in request.items()
            if key != "payment_card_id"
        }

        if is_principal is not None and is_principal not in [0, 1]:
            raise CustomException("El valor de 'is_principal' debe ser 0 o 1.")

        if "is_principal" in update_values and is_principal == 1:
            stmt = (
                update(PaymentCardModel)
                .where(
                    PaymentCardModel.user_id == user_id,
                    PaymentCardModel.active == ACTIVE,
                    PaymentCardModel.is_principal == 1
                )
                .values(is_principal=0)
            )
            is_updated = self.db.update(stmt)

        if update_values:
            self.validations.validate_data(
                update_values, self.fields, is_update=True
            )

            stmt = (
                update(PaymentCardModel)
                .where(
                    PaymentCardModel.payment_card_id == payment_card_id,
                    PaymentCardModel.active == ACTIVE
                )
                .values(**update_values)
            )
            is_updated = self.db.update(stmt)

        return (
            _response({"is_updated": bool(is_updated)}, SUCCESS_STATUS)
            if is_updated
            else _response(
                "No se pudo actualizar la tarjeta.", ERROR_STATUS
            )
        )

    def delete_payment_card(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        payment_card_id = request.get("payment_card_id")

        self.validations.records(
            conn=self.db,
            model=PaymentCardModel,
            pk=payment_card_id,
            error_class=CustomException(
                "No hay tarjetas vinculadas.", NO_DATA_STATUS),
            as_dict=True,
        )

        stmt = (
            update(PaymentCardModel)
            .where(
                PaymentCardModel.payment_card_id == payment_card_id,
                PaymentCardModel.active == ACTIVE
            )
            .values(active=INACTIVE)
        )
        is_deleted = self.db.update(stmt)

        return (
            _response({"is_deleted": bool(is_deleted)}, SUCCESS_STATUS)
            if is_deleted
            else _response(
                "No se pudo desvincular la tarjeta.", ERROR_STATUS
            )
        )
