from typing import Any, Dict
from sqlalchemy import insert, update, select, and_
from Models.User import UserModel
from Models.City import CityModel
from Models.State import StateModel
from Models.Address import AddressModel
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


class Address:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)
        self.fields = {
            "user_id": int,
            "state_id": int,
            "city_id": int,
            "address": str,
        }

    def get_address(self, event: Dict[str, Any]) -> Dict[str, Any]:
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
                AddressModel,
                StateModel.state_name,
                CityModel.city_name,
            )
            .join(
                StateModel,
                and_(
                    AddressModel.state_id == StateModel.state_id,
                    StateModel.active == ACTIVE,
                ),
            )
            .join(
                CityModel,
                and_(
                    AddressModel.city_id == CityModel.city_id,
                    CityModel.active == ACTIVE,
                ),
            )
            .join(
                UserModel,
                and_(
                    AddressModel.user_id == UserModel.user_id,
                    UserModel.active == ACTIVE,
                ),
            )
            .where(
                AddressModel.active == ACTIVE,
                AddressModel.user_id == user_id
            )
        )
        addresses = self.db.query(stmt)

        return (
            _response(addresses.as_dict(), SUCCESS_STATUS)
            if addresses
            else _response("No hay direcciones vinculadas.", NO_DATA_STATUS)
        )

    def add_address(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        user_id = request.get("user_id")
        is_principal = request.get("is_principal", 1)

        self.validations.records(
            conn=self.db,
            model=UserModel,
            pk=user_id,
            error_class=CustomException(
                "No se encontró el usuario.", NO_DATA_STATUS
            ),
            as_dict=True,
        )

        self.validations.validate_data(request, self.fields)

        stmt = insert(AddressModel).values(
            user_id=user_id,
            state_id=request["state_id"],
            city_id=request["city_id"],
            address=request["address"],
            is_principal=is_principal
        )
        address_id = self.db.add(stmt)

        return (
            _response({"address_id": address_id}, CREATED_STATUS)
            if address_id
            else _response("No se pudo vincular la dirección.", ERROR_STATUS)
        )

    def update_address(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        user_id = request.get("user_id")
        address_id = request.get("address_id")
        is_principal = request.get("is_principal")

        self.validations.records(
            conn=self.db,
            model=UserModel,
            pk=user_id,
            error_class=CustomException(
                "No se encontró el usuario.", NO_DATA_STATUS
            ),
            as_dict=True,
        )

        self.validations.records(
            conn=self.db,
            model=AddressModel,
            pk=address_id,
            error_class=CustomException(
                "No hay direcciones vinculadas.", NO_DATA_STATUS
            ),
            as_dict=True,
        )

        updated_values = {
            key: value for key, value in request.items()
            if key != "address_id"
        }

        if is_principal is not None and is_principal not in [0, 1]:
            raise CustomException("El valor de 'is_principal' debe ser 0 o 1.")

        if "is_principal" in updated_values and is_principal == 1:
            stmt = (
                update(AddressModel)
                .where(
                    AddressModel.user_id == user_id,
                    AddressModel.active == ACTIVE,
                    AddressModel.is_principal == 1
                )
                .values(is_principal=0)
            )
            is_updated = self.db.update(stmt)

        if updated_values:
            self.validations.validate_data(
                updated_values, self.fields, is_update=True
            )

            stmt = (
                update(AddressModel)
                .where(
                    AddressModel.address_id == address_id,
                    AddressModel.active == ACTIVE
                )
                .values(**updated_values)
            )
            is_updated = self.db.update(stmt)

        return (
            _response({"is_updated": bool(is_updated)}, SUCCESS_STATUS)
            if is_updated
            else _response(
                "No se pudo actualizar la dirección.", ERROR_STATUS
            )
        )

    def delete_address(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        address_id = request.get("address_id")

        self.validations.records(
            conn=self.db,
            model=AddressModel,
            pk=address_id,
            error_class=CustomException(
                "No hay direcciones vinculadas.", NO_DATA_STATUS
            ),
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

        return (
            _response({"is_deleted": bool(is_deleted)}, SUCCESS_STATUS)
            if is_deleted
            else _response(
                "No se pudo desvincular la dirección.", ERROR_STATUS
            )
        )
