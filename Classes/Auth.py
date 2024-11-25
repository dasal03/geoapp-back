import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy import select
from Models.User import UserModel
from Utils.ExceptionsTools import CustomException
from Utils.GeneralTools import get_input_data
from Utils.Validations import Validations

SECRET_KEY = os.getenv("SECRET_KEY")


class Auth:
    """Class to manage user authentication."""

    def __init__(self, db):
        self.db = db
        self.validations = Validations(self.db)

    def _handle_db_error(self, error: Exception):
        """Handles database errors."""
        return {"statusCode": 500, "data": f"Database error: {str(error)}"}

    def login(self, event):
        """Validate user credentials and return a token if the user exists."""
        try:
            request = get_input_data(event)
            username = request.get("username", "")
            password = request.get("password", "")

            validated = self.validations.validate(
                [
                    self.validations.param(
                        "Username", str, username, min_len=4, max_len=10
                    ),
                    self.validations.param(
                        "Password", str, password, min_len=4, max_len=10
                    ),
                ],
                cast=True,
            )

            if not validated["isValid"]:
                raise CustomException(validated["data"])

            # Fetch user data from the database
            response = self.db.query(
                select(UserModel.user_id, UserModel.password).where(
                    UserModel.username == username, UserModel.active == 1
                )
            ).first()

            if not response:
                return {
                    "statusCode": 400,
                    "data": "Invalid username or password"
                }

            # Compare password hash
            if bcrypt.checkpw(password.encode(), response.password.encode()):
                exp = datetime.utcnow() + timedelta(hours=1)
                token = jwt.encode(
                    {
                        "user_id": response.user_id,
                        "exp": exp,
                    },
                    SECRET_KEY,
                    algorithm="HS256",
                )

                return {"statusCode": 200, "data": {"token": token}}

            return {"statusCode": 400, "data": "Invalid username or password"}

        except Exception as e:
            return self._handle_db_error(e)
