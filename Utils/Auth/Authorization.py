from typing import Dict, Any
from sqlalchemy import select, and_
from Models.User import UserModel
from Models.Role import RoleModel
from Utils.Constants import ACTIVE, FORBIDDEN_STATUS
from Utils.ExceptionsTools import CustomException


class TokenTools:
    """
    Main class for token extraction and user data retrieval.
    """

    def __init__(self, db):
        """Initializing class base attributes."""
        self.db = db

    @staticmethod
    def extract_token(event: Dict[str, Any]) -> str:
        """
        Extracts the Authorization token from event headers.

        Args:
            event (Dict[str, Any]):
                The event data containing the Authorization header.

        Returns:
            str: The extracted token or None if not found.
        """
        return event.get("headers", {}).get("Authorization")

    def get_user_info(self, user_id: int) -> Dict[str, Any]:
        """
        Query and return user information, including role and permissions.

        Args:
            user_id (int): The user ID to query.

        Returns:
            Dict[str, Any]: The user data including role and permissions.

        Raises:
            CustomException: If the user is not found or is inactive.
        """
        stmt = (
            select(
                UserModel.user_id,
                UserModel.username,
                RoleModel.role_name,
                UserModel.profile_img
            )
            .join(
                RoleModel,
                and_(
                    RoleModel.role_id == UserModel.role_id,
                    RoleModel.active == ACTIVE
                )
            )
            .where(
                UserModel.user_id == user_id,
                UserModel.active == ACTIVE
            )
        )

        results = self.db.query(stmt).first()

        if not results:
            raise CustomException(
                "Usuario no encontrado o inactivo.", FORBIDDEN_STATUS
            )

        return results.as_dict()
