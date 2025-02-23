from typing import Any, Dict
from sqlalchemy.sql import func
from sqlalchemy import insert, update, select
from Models.Address import AddressModel
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
from Utils.GeneralTools import get_input_data
from Utils.ExceptionsTools import CustomException


class Address:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)
        self.user = User(db)
        self.fields = {
            "user_id": int,
            "state": str,
            "city": str,
            "address": str,
            "apartment": str,
            "postcode": str,
            "description": str
        }

    def get_address(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        user_id = request.get("user_id")

        conditions = {"active": ACTIVE, **request}
        conditions = {k: v for k, v in conditions.items() if v is not None}

        self.user._validate_user_exists(user_id)

        addresses = self.db.query(
            select(
                AddressModel,
                func.concat(
                    AddressModel.address, " - ",
                    AddressModel.apartment
                ).label("full_address")
            )
            .distinct(AddressModel.address_id).filter_by(**conditions)
        ).as_dict()

        return {
            "statusCode": SUCCESS_STATUS if addresses else NO_DATA_STATUS,
            "data": addresses or "No se encontraron direcciones",
        }

    def add_address(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        user_id = request.get("user_id")

        self.user._validate_user_exists(user_id)
        self.validations.validate_data(request, self.fields)

        self.set_principal_item(user_id)

        stmt = insert(AddressModel).values(
            {key: request.get(key) for key in self.fields}
        )
        address_id = self.db.add(stmt)

        return {
            "statusCode": CREATED_STATUS if address_id else ERROR_STATUS,
            "data": {"address_id": address_id} or {},
        }

    def update_address(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        user_id = request.get("user_id")
        address_id = request.get("address_id")

        self.user._validate_user_exists(user_id)

        self.validations.records(
            conn=self.db,
            model=AddressModel,
            pk=address_id,
            error_class=CustomException(
                "No se encontró la dirección.", NO_DATA_STATUS
            ),
            as_dict=True,
        )

        updated_values = {
            k: v for k, v in request.items()
            if k not in ["address_id", "user_id"]
        }
        print(f"Valores actualizados: {updated_values}")

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
            update(AddressModel).where(
                AddressModel.user_id == user_id,
                AddressModel.address_id == address_id,
                AddressModel.active == ACTIVE,
            ).values(**updated_values)
        )
        is_updated = self.db.update(stmt)

        return {
            "statusCode": SUCCESS_STATUS if is_updated else ERROR_STATUS,
            "data": {"is_updated": bool(is_updated)}
        }

    def delete_address(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        address_id = request.get("address_id")

        self.validations.records(
            conn=self.db,
            model=AddressModel,
            pk=address_id,
            error_class=CustomException(
                "No se encontró la dirección.", NO_DATA_STATUS),
            as_dict=True,
        )

        stmt = (
            update(AddressModel)
            .where(
                AddressModel.address_id == address_id,
                AddressModel.active == ACTIVE
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
            select(AddressModel.address_id)
            .where(
                AddressModel.user_id == user_id,
                AddressModel.is_principal == 1,
                AddressModel.active == ACTIVE,
            )
        ).first()

        if existing_principal:
            self.db.update(
                update(AddressModel)
                .where(
                    AddressModel.address_id ==
                    existing_principal.address_id
                )
                .values(is_principal=0)
            )
