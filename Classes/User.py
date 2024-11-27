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
            raise CustomException(
                "El nombre de usuario ya está en uso.", ERROR_STATUS
            )

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
            _response(SUCCESS_STATUS, user_info)
            if user_info
            else _response(
                FORBIDDEN_STATUS,
                "No se pudo obtener la información del usuario."
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
        stmt = select(UserModel).filter_by(**conditions)
        user_info = self.db.query(stmt).first()

        return (
            _response(SUCCESS_STATUS, user_info.as_dict())
            if user_info
            else _response(NO_DATA_STATUS, "Usuario no encontrado.")
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
        username = request.get("username", None)

        self._check_username_availability(username)
        self._validate_user_data(request, self.fields)

        hashed_password = encrypt_password(request["password"])

        stmt = insert(UserModel).values(
            fullname=request["fullname"],
            username=username,
            password=hashed_password,
        )
        user_id = self.db.add(stmt)

        return (
            _response(CREATED_STATUS, {"user_id": user_id})
            if user_id
            else _response(ERROR_STATUS, "Error al registrar el usuario.")
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
            raise CustomException(
                "No se proporcionó el ID del usuario.", ERROR_STATUS
            )

        self._validate_user_exists(user_id)

        if password and confirm_password:
            if password != confirm_password:
                return _response(ERROR_STATUS, "Las contraseñas no coinciden.")

            request["password"] = encrypt_password(password)
            del request["confirm_password"]

        update_values = {
            key: value
            for key, value in request.items()
            if value is not None
        }

        if not update_values:
            return _response(ERROR_STATUS, "No hay datos para actualizar.")

        self._validate_user_data(update_values, self.fields)

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
            _response(SUCCESS_STATUS, {"updated": bool(updated)})
            if updated
            else _response(ERROR_STATUS, "Error al actualizar el usuario.")
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
            _response(SUCCESS_STATUS, {"deleted": bool(deleted)})
            if deleted
            else _response(ERROR_STATUS, "Error al eliminar el usuario.")
        )

    def _validate_user_data(
        self,
        request: Dict[str, Any],
        fields: Dict[str, type],
    ) -> None:
        """
        Validate user data based on provided fields and expected types.

        Args:
            request (dict): The user data to be validated.
            fields (Dict[str, type]): The expected types for each field.

        Raises:
            CustomException: If the validation fails.
        """
        for field, expected_type in fields.items():
            validate = self.validations.validate([
                self.validations.param(
                    field, expected_type, request.get(field, "")
                )
            ], cast=True)

            if not validate["isValid"]:
                raise CustomException(validate["data"])
