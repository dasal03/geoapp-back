from typing import Any, Dict
from sqlalchemy import insert, select, update
from Models.User import UserModel
from Utils.Auth.Authorization import TokenTools
from Utils.Constants import (
    ACTIVE,
    INACTIVE,
    SUCCESS_STATUS,
    CREATED_STATUS,
    ERROR_STATUS,
    NO_DATA_STATUS,
    FORBIDDEN_STATUS
)
from Utils.ExceptionsTools import CustomException
from Utils.GeneralTools import get_input_data, encrypt_password
from Utils.QueryTools import all_columns_excluding
from Utils.Response import _response
from Utils.Validations import Validations


class User:
    "Class to manage user operations."
    fields = {
        "fullname": str,
        "username": str,
        "password": str,
        "confirm_password": str,
    }

    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)

    def _validate_user_exists(self, user_id: int) -> None:
        """
        Validate if the user exists.

        Args:
            user_id (int):
            The ID of the user to validate.

        Raises:
            CustomException:
            If the user does not exist.
        """
        self.validations.records(
            conn=self.db,
            model=UserModel,
            pk=user_id,
            error_class=CustomException(
                "No se encontró el usuario.", NO_DATA_STATUS
            ),
            as_dict=True,
        )

    def _check_username_availability(self, username: str) -> None:
        """
        Check if the username is available.

        Args:
            username (str):
            The username to check.

        Raises:
            CustomException:
            If the username is not available.
        """
        if self.db.query(
            select(UserModel.username)
            .filter_by(username=username, active=ACTIVE)
        ).first():
            raise CustomException("El nombre de usuario ya está en uso.")

    def user_data_by_token(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve user data using the token provided in the event.

        Args:
            event (Dict[str, Any]):
            The event data containing the token.

        Returns:
            Dict[str, Any]:
            User data.
        """
        user_info = TokenTools(self.db).extract_user_info(event)
        return (
            _response(user_info, SUCCESS_STATUS)
            if user_info
            else _response(
                "No se pudo obtener la información del usuario.",
                FORBIDDEN_STATUS
            )
        )

    def get_user_data(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get user data based on provided parameters.

        Args:
            event (Dict[str, Any]):
            The event data containing the user data to retrieve.

        Returns:
            Dict[str, Any]:
            Filtered user data.
        """
        conditions = {"active": ACTIVE, **get_input_data(event)}
        stmt = select(
            *all_columns_excluding(UserModel, "password")
        ).filter_by(**conditions)
        user_info = self.db.query(stmt).first()

        return (
            _response(user_info.as_dict(), SUCCESS_STATUS)
            if user_info
            else _response({}, NO_DATA_STATUS)
        )

    def register_user(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new user in the database.

        Args:
            event (Dict[str, Any]):
            The event data containing the user data to register.

        Returns:
            Dict[str, Any]:
            A response indicating the success or failure
            of the registration operation.
        """
        request = get_input_data(event)
        username = request.get("username", "")

        self._check_username_availability(username)
        self.validations.validate_data(request, self.fields)

        hashed_password = encrypt_password(request["password"])

        stmt = insert(UserModel).values(
            fullname=request.get("fullname", ""),
            username=username,
            password=hashed_password,
        )
        user_id = self.db.add(stmt)

        return (
            _response({"user_id": user_id}, CREATED_STATUS)
            if user_id
            else _response("Error al registrar el usuario.", ERROR_STATUS)
        )

    def update_user(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user data in the database.

        Args:
            event (Dict[str, Any]):
            The event data containing the user ID and the data to update.

        Returns:
            Dict[str, Any]:
            A response indicating the success or failure
            of the update operation.
        """
        request = get_input_data(event)
        user_id = request.pop("user_id", 0)
        password = request.get("password", None)
        confirm_password = request.get("confirm_password", None)

        if not user_id:
            raise CustomException("No se proporcionó el ID del usuario.")

        self._validate_user_exists(user_id)

        if password:
            if password != confirm_password:
                raise CustomException(
                    "Las contraseñas no coinciden." if confirm_password else
                    "La confirmación de la contraseña es requerida."
                )

            request["password"] = encrypt_password(password)
            request.pop("confirm_password", None)

        update_values = {
            key: value
            for key, value in request.items()
            if value is not None
        }

        if not update_values:
            raise CustomException(
                "No se proporcionaron datos para actualizar."
            )

        self.validations.validate_data(
            update_values, self.fields, is_update=True
        )

        stmt = (
            update(UserModel)
            .where(
                UserModel.user_id == user_id,
                UserModel.active == ACTIVE,
            )
            .values(**update_values)
        )
        updated = self.db.update(stmt)

        return (
            _response({"updated": bool(updated)}, SUCCESS_STATUS)
            if updated
            else _response("Error al actualizar el usuario.", ERROR_STATUS)
        )

    def delete_user(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete user data from the database.

        Args:
            event (Dict[str, Any]):
            The event data containing the user ID to delete.

        Returns:
            Dict[str, Any]:
            A response indicating the success or failure
            of the deletion operation.
        """
        user_id = get_input_data(event).get("user_id", 0)
        if not user_id:
            raise CustomException("No se proporcionó el ID del usuario.")

        self._validate_user_exists(user_id)

        stmt = (
            update(UserModel)
            .where(
                UserModel.user_id == user_id,
                UserModel.active == ACTIVE,
            )
            .values(active=INACTIVE)
        )
        deleted = self.db.update(stmt)

        return (
            _response({"deleted": bool(deleted)}, SUCCESS_STATUS)
            if deleted
            else _response("Error al eliminar el usuario.", ERROR_STATUS)
        )
