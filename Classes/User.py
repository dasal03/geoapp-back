import os
import uuid
from typing import Any, Dict
from sqlalchemy.sql import func
from sqlalchemy.orm import aliased
from sqlalchemy import insert, select, update, and_
from Models.Address import AddressModel
from Models.City import CityModel
from Models.DocumentType import DocumentTypeModel
from Models.Gender import GenderModel
from Models.State import StateModel
from Models.User import UserModel
from Utils.Auth.Authorization import TokenTools
from Utils.Constants import (
    ACTIVE,
    INACTIVE,
    SUCCESS_STATUS,
    CREATED_STATUS,
    ERROR_STATUS,
    UNAUTHORIZED_STATUS,
    NO_DATA_STATUS,
    FORBIDDEN_STATUS,
)
from Utils.ExceptionsTools import CustomException
from Utils.GeneralTools import (
    get_input_data, encrypt_password, decrypt_password
)
from Utils.QueryTools import all_columns_excluding
from Utils.Response import _response
from Utils.S3Manager import S3Manager
from Utils.Validations import Validations


class User:
    "Class to manage user operations."

    def __init__(self, db):
        self.db = db
        self.bucket_name = os.getenv("BUCKET_NAME")
        self.s3_manager = S3Manager()
        self.validations = Validations(db)
        self.fields = {
            "first_name": str,
            "last_name": str,
            "username": str,
            "password": str,
            "confirm_password": str,
            "email": str,
            "phone_number": str,
            "date_of_birth": str,
            "gender_id": int,
            "document_type_id": int,
            "document_number": str,
            "state_of_issue_id": int,
            "city_of_issue_id": int,
            "date_of_issue": str,
        }

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
                "No se encontró el usuario.", NO_DATA_STATUS),
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
            event (Dict[str, Any]): The event data containing the token.

        Returns:
            Dict[str, Any]: User data, including permissions.
        """
        try:
            user_info = TokenTools(self.db).extract_user_info(event)

            return (
                _response(user_info, SUCCESS_STATUS)
                if user_info
                else _response(
                    "No se pudo obtener la información del usuario.",
                    FORBIDDEN_STATUS
                )
            )
        except CustomException as e:
            return _response(str(e), e.status_code)

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
        issue_state = aliased(StateModel)
        issue_city = aliased(CityModel)

        stmt = (
            select(
                *all_columns_excluding(UserModel, "password"),
                func.concat(
                    UserModel.first_name,
                    " ",
                    UserModel.last_name,
                ).label("full_name"),
                GenderModel.gender_id,
                GenderModel.gender_name,
                DocumentTypeModel.description.label("document_type"),
                issue_city.city_name.label("city_of_issue"),
                issue_state.state_name.label("state_of_issue"),
            )
            .filter_by(**conditions)
            .join(
                GenderModel,
                and_(
                    GenderModel.gender_id == UserModel.gender_id,
                    GenderModel.active == ACTIVE,
                ),
                isouter=True,
            )
            .join(
                DocumentTypeModel,
                and_(
                    DocumentTypeModel.document_type_id ==
                    UserModel.document_type_id,
                    DocumentTypeModel.active == ACTIVE,
                ),
                isouter=True,
            )
            .join(
                AddressModel,
                and_(
                    AddressModel.user_id == UserModel.user_id,
                    AddressModel.active == ACTIVE,
                ),
                isouter=True,
            )
            .join(
                issue_state,
                and_(
                    UserModel.state_of_issue_id == issue_state.state_id,
                    issue_state.active == ACTIVE,
                ),
                isouter=True,
            )
            .join(
                issue_city,
                and_(
                    UserModel.city_of_issue_id == issue_city.city_id,
                    issue_city.active == ACTIVE,
                ),
                isouter=True,
            )
        )
        user_info = self.db.query(stmt).first().as_dict()

        if user_info and user_info["profile_img"]:
            user_info["profile_img"] = self.s3_manager.presigned_download_file(
                self.bucket_name, user_info["profile_img"]
            )["data"]["url"]

        return (
            _response(user_info, SUCCESS_STATUS)
            if user_info
            else _response(
                "No se encontró la información del usuario.", NO_DATA_STATUS)
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

        profile_img = request.get("profile_img", None)
        if profile_img:
            profile_img = profile_img.split(",")[1]

            upload_img = self.s3_manager.upload_base64_file(
                self.bucket_name,
                f"profile_img_{uuid.uuid4()}.jpg",
                profile_img,
                "profile_imgs/",
            )
            profile_img = upload_img["data"]["s3_route"]

        stmt = insert(UserModel).values(
            first_name=request.get("first_name", None),
            last_name=request.get("last_name", None),
            username=username,
            password=hashed_password,
            email=request.get("email", ""),
            phone_number=request.get("phone_number", ""),
            date_of_birth=request.get("date_of_birth", None),
            gender_id=request.get("gender_id", 0),
            document_type_id=request.get("document_type_id", 0),
            document_number=request.get("document_number", ""),
            state_of_issue_id=request.get("state_of_issue_id", 0),
            city_of_issue_id=request.get("city_of_issue_id", 0),
            date_of_issue=request.get("date_of_issue", None),
            role_id=request.get("role_id", 2),
            profile_img=profile_img if profile_img else None,
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

        if "profile_img" in request:
            request["profile_img"] = self.s3_manager.upload_base64_file(
                self.bucket_name,
                f"profile_img_{uuid.uuid4()}.jpg",
                request.pop("profile_img"),
            )

        if password:
            if password != confirm_password:
                raise CustomException(
                    "Las contraseñas no coinciden."
                    if confirm_password
                    else "La confirmación de la contraseña es requerida."
                )

            request["password"] = encrypt_password(password)
            request.pop("confirm_password", None)

        update_values = {
            key: value for key, value in request.items() if value is not None
        }

        if not update_values:
            raise CustomException(
                "No se proporcionaron datos para actualizar.")

        self.validations.validate_data(
            update_values, self.fields, is_update=True)

        stmt = (
            update(UserModel)
            .where(
                UserModel.user_id == user_id,
                UserModel.active == ACTIVE,
            )
            .values(**update_values)
        )
        is_updated = self.db.update(stmt)

        return (
            _response({"is_updated": bool(is_updated)}, SUCCESS_STATUS)
            if is_updated
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
        user_img = self._get_user_img(user_id)

        if user_img.profile_img:
            self._delete_profile_image(user_img.profile_img)

        stmt = (
            update(UserModel)
            .where(
                UserModel.user_id == user_id,
                UserModel.active == ACTIVE,
            )
            .values(active=INACTIVE)
        )
        is_deleted = self.db.update(stmt)

        return (
            _response({"is_deleted": bool(is_deleted)}, SUCCESS_STATUS)
            if is_deleted
            else _response("Error al eliminar el usuario.", ERROR_STATUS)
        )

    def change_password(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        user_id = event.get("user_id")
        password = request.get("password")
        new_password = request.get("new_password")

        if not user_id:
            raise CustomException("No se proporcionó el ID del usuario.")

        self._validate_user_exists(user_id)

        if not password:
            raise CustomException("La contraseña es requerida.")

        if not new_password:
            raise CustomException("La nueva contraseña es requerida.")

        if password == new_password:
            raise CustomException(
                "La nueva contraseña debe ser diferente a la actual.")

        self._verify_password(user_id, password)

        stmt = (
            update(UserModel)
            .where(
                UserModel.user_id == user_id,
                UserModel.active == ACTIVE,
            )
            .values(password=encrypt_password(new_password))
        )
        is_updated = self.db.update(stmt)

        return (
            _response({"is_updated": bool(is_updated)}, SUCCESS_STATUS)
            if is_updated
            else _response("Error al actualizar la contraseña.", ERROR_STATUS)
        )

    def _verify_password(self, user_id: int, password: str) -> None:
        user_data = self.db.query(
            select(UserModel.password)
            .filter_by(user_id=user_id)
        ).first()

        if not user_data:
            raise CustomException("El usuario no existe.", NO_DATA_STATUS)
        if not decrypt_password(password, user_data.password):
            raise CustomException(
                "La contraseña es incorrecta.", UNAUTHORIZED_STATUS
            )
