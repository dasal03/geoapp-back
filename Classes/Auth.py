import os
import jwt
from typing import Any, Dict
from datetime import datetime, timedelta
from sqlalchemy import select
from Models.User import UserModel
from Utils.Constants import ACTIVE, SUCCESS_STATUS, UNAUTHORIZED_STATUS
from Utils.ExceptionsTools import CustomException
from Utils.GeneralTools import get_input_data, decrypt_password
from Utils.Validations import Validations


class Auth:
    """Class to manage user authentication."""

    def __init__(self, db):
        self.db = db
        self.secret_key = os.getenv("SECRET_KEY")
        self.validations = Validations(self.db)
        self.fields = {"username": str, "password": str}

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
        self.validations.validate_data(request, self.fields)

        user = self._get_user_by_username(request.get("username"))
        if not user or not decrypt_password(
            request["password"], user.password
        ):
            raise CustomException(
                "Credenciales incorrectas", UNAUTHORIZED_STATUS
            )

        token = self._generate_token(user.user_id)

        return {
            "statusCode": SUCCESS_STATUS if user else UNAUTHORIZED_STATUS,
            "data": {"token": token}
            if user else "No se pudo generar el token",
        }

    def _get_user_by_username(self, username: str) -> UserModel:
        stmt = select(UserModel).filter_by(username=username, active=ACTIVE)
        return self.db.query(stmt).first()

    def _generate_token(self, user_id: int) -> str:
        """Generate a JWT token with expiration for the user."""
        payload = {
            "user_id": user_id, "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
