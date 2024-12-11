from typing import Any, Dict
from sqlalchemy import insert, update, select, and_
from Models.Address import AddressModel
from Models.City import CityModel
from Models.State import StateModel
from Models.User import UserModel
from Utils.Constants import (
    ACTIVE,
    INACTIVE,
    SUCCESS_STATUS,
    CREATED_STATUS,
    ERROR_STATUS,
    NO_DATA_STATUS,
)
from Utils.ExceptionsTools import CustomException
from Utils.GeneralTools import get_input_data
from Utils.Response import _response
from Utils.Validations import Validations


class Address:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)
        self.fields = {
            "state_id": int,
            "city_id": int,
            "address": str,
            "user_id": int
        }

    def get_address(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        user_id = request.get("user_id")

        if not user_id:
            raise CustomException("No se proporcionó el ID del usuario.")

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
            else _response("No se encontraron direcciones.", NO_DATA_STATUS)
        )

    def register_address(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        user_id = request.get("user_id")
        self.validations.validate_data(request, self.fields)

        stmt = insert(AddressModel).values(
            user_id=user_id,
            state_id=request["state_id"],
            city_id=request["city_id"],
            address=request["address"],
            principal_address=ACTIVE,
        )
        address_id = self.db.add(stmt)

        return (
            _response({"address_id": address_id}, CREATED_STATUS)
            if address_id
            else _response("No se pudo crear la dirección.", ERROR_STATUS)
        )

    def update_address(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        address_id = request.get("address_id")

        update_values = {
            key: value for key, value in request.items() if value is not None
        }
        self.validations.validate_data(
            update_values, self.fields, is_update=True
        )

        stmt = (
            update(AddressModel)
            .where(AddressModel.address_id == address_id)
            .values(**update_values)
        )
        updated = self.db.add(stmt)

        return (
            _response({"updated": bool(updated)}, SUCCESS_STATUS)
            if updated
            else _response("No se pudo actualizar la dirección.", ERROR_STATUS)
        )

    def delete_address(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        address_id = request.get("address_id")

        stmt = (
            update(AddressModel)
            .where(AddressModel.address_id == address_id)
            .values(active=INACTIVE)
        )
        deleted = self.db.update(stmt)

        return (
            _response({"deleted": bool(deleted)}, SUCCESS_STATUS)
            if deleted
            else _response("No se pudo eliminar la dirección.", ERROR_STATUS)
        )
