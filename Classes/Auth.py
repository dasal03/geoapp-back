import os
import jwt
from typing import Any, Dict
from datetime import datetime, timedelta
from sqlalchemy import select
from Models.User import UserModel
from Utils.Constants import ACTIVE, SUCCESS_STATUS, UNAUTHORIZED_STATUS
from Utils.ExceptionsTools import CustomException
from Utils.GeneralTools import get_input_data, decrypt_password
from Utils.Response import _response
from Utils.Validations import Validations


class Auth:
    """Class to manage user authentication."""

    def __init__(self, db):
        self.db = db
        self.secret_key = os.getenv("SECRET_KEY")
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
        print(f"request: {request}")
        self._validate_login_request(request)

        user_data = self._fetch_user(request["username"])
        self._verify_password(request["password"], user_data.password)

        token = self._generate_token(user_data.user_id)
        if not token:
            raise CustomException(
                "Error al generar el token", UNAUTHORIZED_STATUS
            )

        return _response({"token": token}, SUCCESS_STATUS)

    def _validate_login_request(self, request: Dict[str, Any]) -> None:
        """Validate the login request fields."""
        fields = {"username": str, "password": str}
        self.validations.validate_data(request, fields)

    def _fetch_user(self, username: str):
        """Fetch user data from the database."""
        user_data = self.db.query(
            select(UserModel)
            .where(UserModel.username == username, UserModel.active == ACTIVE)
        ).first()
        if not user_data:
            raise CustomException("El usuario no existe", UNAUTHORIZED_STATUS)
        return user_data

    def _verify_password(
        self, input_password: str, stored_password: str
    ) -> None:
        """Verify if the provided password matches the stored hash."""
        if not decrypt_password(input_password, stored_password):
            raise CustomException(
                "Contraseña incorrecta", UNAUTHORIZED_STATUS
            )

    def _generate_token(self, user_id: int) -> str:
        """
        Generate a JWT token for the user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            str: The generated JWT token.
        """
        print(f"secret_key: {self.secret_key}")
        exp = datetime.utcnow() + timedelta(hours=1)
        return jwt.encode(
            {"user_id": user_id, "exp": exp},
            self.secret_key,
            algorithm="HS256",
        )
