from typing import Any, Dict
from sqlalchemy import insert, select, update
from sqlalchemy.sql import func
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
        "first_name": str,
        "middle_name": str,
        "last_name": str,
        "username": str,
        "password": str,
        "confirm_password": str,
        "email": str,
        "country_id": int,
        "phone_number": str,
        "address": str,
        "document_type_id": int,
        "document_number": str,
        "place_of_issue_id": int,
        "issue_date": str,
        "issue_state_id": int,
        "expiry_date": str,
        "issue_authority": str,
        "date_of_birth": str,
        "gender_id": int,
        "role_id": int
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
            *all_columns_excluding(UserModel, "password"),
            func.concat(
                UserModel.first_name, " ",
                UserModel.middle_name, " ",
                UserModel.last_name
            ).label("full_name")
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
            first_name=request.get("first_name", None),
            middle_name=request.get("middle_name", None),
            last_name=request.get("last_name", None),
            username=username,
            password=hashed_password,
            email=request.get("email", ""),
            country_id=request.get("country_id", 0),
            phone_number=request.get("phone_number", ""),
            address=request.get("address", ""),
            document_type_id=request.get("document_type_id", 0),
            document_number=request.get("document_number", ""),
            place_of_issue_id=request.get("place_of_issue_id", 0),
            issue_date=request.get("issue_date"),
            issue_state_id=request.get("issue_state_id", 0),
            expiry_date=request.get("expiry_date"),
            issue_authority=request.get("issue_authority", None),
            date_of_birth=request.get("date_of_birth"),
            gender_id=request.get("gender_id", 0),
            role_id=request.get("role_id", 2),
            active=request.get("active", 1),
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
