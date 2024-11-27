import os
import jwt
from typing import Any, Dict
from datetime import datetime, timedelta
from sqlalchemy import select
from Models.User import UserModel
from Utils.Constants import (
    ACTIVE,
    SUCCESS_STATUS,
    UNAUTHORIZED_STATUS
)
from Utils.ExceptionsTools import CustomException
from Utils.GeneralTools import get_input_data, decrypt_password
from Utils.Response import _response
from Utils.Validations import Validations

SECRET_KEY = os.getenv("SECRET_KEY")


class Auth:
    """Class to manage user authentication."""

    def __init__(self, db):
        self.db = db
        self.validations = Validations(self.db)

    def login(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate user credentials and return a token if the user exists.

        Args:
            event (Dict[str, Any]):
            The event data containing the user credentials.

        Returns:
            Dict[str, Any]: The response containing the token or error message.
        """
        request = get_input_data(event)
        fields = {
            "username": str,
            "password": str
        }
        self._validate_user_data(request, fields)

        # Fetch user data from the database
        user_data = self.db.query(
            select(UserModel.user_id, UserModel.password)
            .where(
                UserModel.username == request["username"],
                UserModel.active == ACTIVE
            )
        ).first()

        if not user_data:
            return _response(UNAUTHORIZED_STATUS, "Usuario inexistente")

        # Compare password hash
        if not decrypt_password(request["password"], user_data.password):
            return _response(UNAUTHORIZED_STATUS, "Contraseña incorrecta")

        # Generate JWT token
        token = self._generate_token(user_data.user_id)
        return (
            _response(SUCCESS_STATUS, {"token": token})
            if token
            else _response(UNAUTHORIZED_STATUS, "Error al generar el token")
        )

    def _generate_token(self, user_id: int) -> str:
        """
        Generate a JWT token for the user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            str: The generated JWT token.
        """
        exp = datetime.utcnow() + timedelta(hours=1)
        return jwt.encode(
            {"user_id": user_id, "exp": exp},
            SECRET_KEY,
            algorithm="HS256",
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
                )], cast=True,
            )

            if not validate["isValid"]:
                raise CustomException(validate["data"])
