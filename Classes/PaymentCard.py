from typing import Any, Dict
from sqlalchemy import insert, select, update
from Models.PaymentCard import PaymentCardModel
from Classes.User import User
from Utils.Constants import (
    ACTIVE,
    INACTIVE,
    SUCCESS_STATUS,
    CREATED_STATUS,
    ERROR_STATUS,
    NO_DATA_STATUS,
)
from Utils.Validations import Validations
from Utils.GeneralTools import get_input_data, encrypt_field
from Utils.ExceptionsTools import CustomException


class PaymentCard:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)
        self.user = User(db)
        self.fields = {
            "user_id": int, "name": str, "number": str,
            "expiry": str, "cvc": str
        }

    def get_user_cards(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        user_id = request.get("user_id")

        conditions = {"active": ACTIVE, **request}
        conditions = {k: v for k, v in conditions.items() if v is not None}

        self.user._validate_user_exists(user_id)

        payment_cards = self.db.query(
            select(PaymentCardModel).filter_by(**conditions)
        ).as_dict()

        return {
            "statusCode": SUCCESS_STATUS if payment_cards else NO_DATA_STATUS,
            "data": payment_cards or "No se encontraron tarjetas.",
        }

    def add_payment_card(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        user_id = request.get("user_id")

        self.user._validate_user_exists(user_id)
        self.validations.validate_data(request, self.fields)

        self.set_principal_item(user_id)

        payment_card_data = {
            key: request[key]
            for key in self.fields
        }

        payment_card_data.update({
            "cvc": encrypt_field(payment_card_data["cvc"])
        })

        stmt = insert(PaymentCardModel).values(**payment_card_data)
        payment_card_id = self.db.add(stmt)

        return {
            "statusCode": CREATED_STATUS if payment_card_id else ERROR_STATUS,
            "data": {"payment_card_id": payment_card_id} or {},
        }

    def update_payment_card(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        user_id = request.get("user_id")
        payment_card_id = request.get("payment_card_id")

        self.user._validate_user_exists(user_id)

        self.validations.records(
            conn=self.db,
            model=PaymentCardModel,
            pk=payment_card_id,
            error_class=CustomException(
                "No se encontró la tarjeta.", NO_DATA_STATUS),
            as_dict=True,
        )

        if request.get("cvc"):
            request["cvc"] = encrypt_field(request["cvc"])

        updated_values = {
            key: value for key, value in request.items()
            if value is not None
            and key not in ["payment_card_id", "user_id"]
        }

        if request.get("is_principal") == 1:
            self.set_principal_item(user_id)

        if not updated_values:
            raise CustomException(
                "No se proporcionaron datos para actualizar."
            )

        self.validations.validate_data(
            updated_values, self.fields, is_update=True
        )

        stmt = (
            update(PaymentCardModel).where(
                PaymentCardModel.user_id == user_id,
                PaymentCardModel.payment_card_id == payment_card_id,
                PaymentCardModel.active == ACTIVE
            ).values(**updated_values)
        )
        is_updated = self.db.update(stmt)

        return {
            "statusCode": SUCCESS_STATUS if is_updated else ERROR_STATUS,
            "data": {"is_updated": bool(is_updated)},
        }

    def delete_payment_card(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        payment_card_id = request.get("payment_card_id")

        self.validations.records(
            conn=self.db,
            model=PaymentCardModel,
            pk=payment_card_id,
            error_class=CustomException(
                "No se encontró la tarjeta.", NO_DATA_STATUS),
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

        return {
            "statusCode": SUCCESS_STATUS if is_deleted else ERROR_STATUS,
            "data": {"is_deleted": bool(is_deleted)}
        }

    def set_principal_item(self, user_id):
        existing_principal = self.db.query(
            select(PaymentCardModel.payment_card_id)
            .where(
                PaymentCardModel.user_id == user_id,
                PaymentCardModel.is_principal == 1,
                PaymentCardModel.active == ACTIVE
            )
        ).first()

        if existing_principal:
            self.db.update(
                update(PaymentCardModel)
                .where(
                    PaymentCardModel.payment_card_id ==
                    existing_principal.payment_card_id
                )
                .values(is_principal=0)
            )
