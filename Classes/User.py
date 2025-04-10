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
)
from Utils.ExceptionsTools import CustomException
from Utils.GeneralTools import get_input_data, encrypt_field
from Utils.QueryTools import all_columns_excluding
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
            "first_name": str, "last_name": str, "username": str,
            "password": str, "confirm_password": str, "email": str,
            "phone_number": str, "date_of_birth": str, "gender_id": int,
            "document_type_id": int, "document_number": str,
            "state_of_issue_id": int, "city_of_issue_id": int,
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
        user_info = TokenTools(self.db).get_user_info(event.get("user_id", 0))

        return {
            "statusCode": SUCCESS_STATUS if user_info else UNAUTHORIZED_STATUS,
            "data": user_info or {}
        }

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
        conditions = {k: v for k, v in conditions.items() if v is not None}

        issue_state, issue_city = aliased(StateModel), aliased(CityModel)

        stmt = select(
            *all_columns_excluding(UserModel, ["password"]),
            func.concat(
                UserModel.first_name, " ", UserModel.last_name
            ).label("full_name"),
            GenderModel.gender_id,
            GenderModel.gender_name,
            DocumentTypeModel.description.label("document_type"),
            issue_city.city_name.label("city_of_issue"),
            issue_state.state_name.label("state_of_issue"),
        ).distinct(UserModel.user_id).filter_by(**conditions)

        join_conditions = [
            (GenderModel, GenderModel.gender_id == UserModel.gender_id),
            (DocumentTypeModel,
             DocumentTypeModel.document_type_id == UserModel.document_type_id),
            (AddressModel, AddressModel.user_id == UserModel.user_id),
            (issue_state, UserModel.state_of_issue_id == issue_state.state_id),
            (issue_city, UserModel.city_of_issue_id == issue_city.city_id),
        ]

        for model, condition in join_conditions:
            stmt = stmt.join(
                model, and_(condition, model.active == ACTIVE), isouter=True
            )

        query_result = self.db.query(stmt).as_dict()

        if "user_id" in conditions:
            user_info = query_result[0] if query_result else None
        else:
            user_info = query_result or []

        def process_profile_image(user):
            if user and user.get("profile_img"):
                user["profile_img"] = self.s3_manager.presigned_download_file(
                    self.bucket_name, user["profile_img"]
                ).get("data", {}).get("url")

        if isinstance(user_info, list):
            for user in user_info:
                process_profile_image(user)
        else:
            process_profile_image(user_info)

        status_code = SUCCESS_STATUS if user_info else NO_DATA_STATUS
        data = user_info if user_info else "No se encontraron datos."

        return {"statusCode": status_code, "data": data}

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
        self._check_username_availability(request.get("username", ""))

        if "alternative_email" in request:
            self.fields["alternative_email"] = str

        self.validations.validate_data(request, self.fields)

        profile_img = request.get("profile_img")

        if profile_img:
            profile_img = self.s3_manager.upload_base64_file(
                self.bucket_name,
                f"profile_img_{uuid.uuid4()}.jpg",
                profile_img.split(",")[1],
                "profile_imgs/",
            )["data"]["s3_route"]

        user_data = {
            key: request[key]
            for key in self.fields
            if key not in ["confirm_password", "password"]
        }

        user_data.update({
            "password": encrypt_field(request["password"]),
            "role_id": request.get("role_id", 2),
            "profile_img": profile_img,
        })

        stmt = insert(UserModel).values(**user_data)
        user_id = self.db.add(stmt)

        return {
            "statusCode": CREATED_STATUS if user_id else ERROR_STATUS,
            "data": {"user_id": user_id} if user_id else {},
        }

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

        if not user_id:
            raise CustomException("No se proporcionó el ID del usuario.")

        self._validate_user_exists(user_id)

        if "profile_img" in request:
            request["profile_img"] = self.s3_manager.upload_base64_file(
                self.bucket_name,
                f"profile_img_{uuid.uuid4()}.jpg",
                request.pop("profile_img"),
                "profile_imgs/",
            )

        if request.get("password"):
            if request["password"] != request.get("confirm_password"):
                raise CustomException(
                    "Las contraseñas no coinciden o falta confirmación."
                )
            request["password"] = encrypt_field(request["password"])

        update_values = {
            key: value for key, value in request.items()
            if value is not None
            and key not in ["user_id", "confirm_password"]
        }

        if not update_values:
            raise CustomException(
                "No se proporcionaron datos para actualizar."
            )

        self.validations.validate_data(
            update_values, self.fields, is_update=True
        )

        is_updated = self.db.update(
            update(UserModel)
            .where(UserModel.user_id == user_id, UserModel.active == ACTIVE)
            .values(**update_values)
        )

        return {
            "statusCode": SUCCESS_STATUS if is_updated else ERROR_STATUS,
            "data": {"is_updated": bool(is_updated)},
        }

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

        is_deleted = self.db.update(
            update(UserModel)
            .where(
                UserModel.user_id == user_id,
                UserModel.active == ACTIVE,
            )
            .values(active=INACTIVE)
        )

        return {
            "statusCode": SUCCESS_STATUS if is_deleted else ERROR_STATUS,
            "data": {"is_deleted": bool(is_deleted)},
        }
