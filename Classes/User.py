# import hashlib
import bcrypt
from sqlalchemy import insert, select, update
from Models.User import UserModel
from Utils.Auth.Authorization import TokenTools
from Utils.Validations import Validations
from Utils.GeneralTools import get_input_data
from Utils.ExceptionsTools import CustomException
from sqlalchemy.exc import SQLAlchemyError


class User:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)

    def _handle_db_error(self, error: SQLAlchemyError):
        """Handles SQLAlchemy errors."""
        return {
            "statusCode": 500,
            "data": f"Error en la base de datos: {str(error)}"
        }

    def user_data_by_token(self, event):
        """
        Retrieve user data using the token provided in the event.

        Args:
            event (dict): The event of the request.

        Returns:
            dict: API response with the status code and user data.
        """
        try:
            token_tools = TokenTools(self.db)
            user_info = token_tools.extract_user_info(event)

            if user_info:
                return {
                    "statusCode": 200,
                    "data": {
                        "user_id": user_info["user_id"],
                        "username": user_info["username"],
                        "fullname": user_info["fullname"],
                    },
                }

            return {
                "statusCode": 400,
                "data": "El token no contiene información válida.",
            }
        except SQLAlchemyError as e:
            return self._handle_db_error(e)

    def get_user_data(self, event):
        """
        Get user data based on the request parameters.

        Args:
            event (dict): The event containing user query parameters.

        Returns:
            dict: API response with the status code and user data.
        """
        try:
            request = get_input_data(event)
            conditions = {"active": 1}

            for key, value in request.items():
                conditions[key] = value

            stmt = select(UserModel).filter_by(**conditions)
            user_info = self.db.query(stmt).first()

            if user_info:
                return {"statusCode": 200, "data": user_info.as_dict()}

            return {"statusCode": 404, "data": "Usuario no encontrado."}
        except SQLAlchemyError as e:
            return self._handle_db_error(e)

    def register_user(self, event):
        """
        Register a new user in the database.

        Args:
            event (dict): The event containing user registration data.

        Returns:
            dict: API response with the status code and user ID.
        """
        try:
            request = get_input_data(event)
            fullname = request.get("fullname", "")
            username = request.get("username", "")
            password = request.get("password", "")
            confirm_password = request.get("confirm_password", "")

            validate = self.validations.validate(
                [
                    self.validations.param(
                        "Nombre completo", str, fullname, min_len=4, max_len=50
                    ),
                    self.validations.param(
                        "Usuario", str, username, min_len=4, max_len=10
                    ),
                    self.validations.param(
                        "Contraseña", str, password, min_len=4, max_len=10
                    ),
                ],
                cast=True,
            )

            if not validate["isValid"]:
                raise CustomException(validate["data"])

            self.validate_username_exist(username)

            if password != confirm_password:
                raise CustomException("Las contraseñas no coinciden.")

            # Hash password with bcrypt for better security
            hashed_password = bcrypt.hashpw(
                password.encode(), bcrypt.gensalt()
            )

            user_id = self.db.add(
                insert(UserModel).values(
                    fullname=fullname,
                    username=username,
                    password=hashed_password
                )
            )

            if user_id:
                return {"statusCode": 201, "data": {"user_id": user_id}}

            return {
                "statusCode": 400,
                "data": "Error al registrar el usuario."
            }
        except SQLAlchemyError as e:
            return self._handle_db_error(e)

    def update_user(self, event):
        """
        Update user password.

        Args:
            event (dict): The event containing user update data.

        Returns:
            dict: API response with the status code.
        """
        try:
            request = get_input_data(event)
            user_id = request.get("user_id", 0)
            password = request.get("password", "")
            confirm_password = request.get("confirm_password", "")

            validate = self.validations.validate(
                [
                    self.validations.param(
                        "Contraseña", str, password, min_len=4, max_len=10
                    ),
                    self.validations.param(
                        "Confirmar contraseña",
                        str,
                        confirm_password,
                        min_len=4,
                        max_len=10,
                    ),
                ],
                cast=True,
            )

            if not validate["isValid"]:
                raise CustomException(validate["data"])

            if password != confirm_password:
                raise CustomException("Las contraseñas no coinciden.")

            hashed_password = bcrypt.hashpw(
                password.encode(), bcrypt.gensalt()
            )

            self.db.update(
                update(UserModel)
                .where(UserModel.user_id == user_id)
                .values(password=hashed_password)
            )

            return {"statusCode": 200, "data": {}}
        except SQLAlchemyError as e:
            return self._handle_db_error(e)

    def validate_username_exist(self, username: str) -> None:
        """
        Validate if the username already exists.

        Args:
            username (str): The username to check for existence.

        Raises:
            CustomException: If the username exists or is invalid.
        """
        try:
            user = self.db.query(
                select(UserModel.username)
                .filter_by(username=username, active=1)
            ).first()

            if user:
                raise CustomException(
                    "El nombre de usuario ya se encuentra en uso.", 400
                )
        except SQLAlchemyError as e:
            raise CustomException(
                f"Error al verificar el nombre de usuario: {str(e)}", 500
            )
