from typing import Dict, Any
from sqlalchemy import select
from Models.User import UserModel
from Models.Role import RoleModel
from Models.Permission import PermissionModel
from Models.RolePermission import RolePermissionModel
from Utils.Constants import ACTIVE, FORBIDDEN_STATUS
from Utils.ExceptionsTools import CustomException


class TokenTools:
    """
    Main class for token extraction data.
    """

    def __init__(self, db):
        """Initializing class base attributes."""
        self.db = db
        self.token = {}

    @staticmethod
    def extract_token(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract token from the event.

        Args:
            event (Dict[str, Any]):
                The event data containing the Authorization header.

        Returns:
            Dict[str, Any]: The token extracted from the event.
        """
        token = {}
        # Extracting token authorizer data from lambda event
        if (
            isinstance(event, dict)
            and "Authorization" in event.get("headers", {})
        ):
            token = event["headers"]["Authorization"]
        return token

    def extract_user_info(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract user information from the event using user ID
        and retrieve permissions based on the user's role.

        Args:
            event (Dict[str, Any]): The event data containing user details.

        Returns:
            Dict[str, Any]: The user information, including permissions.

        Raises:
            CustomException: If the user is not found or is disabled.
        """
        user_id = event.get("user_id", 0)
        user_info = self.get_user_info(user_id)

        # role_id = user_info.get("role_id")
        # permissions_list = self.get_role_permissions(role_id)
        # user_info["permissions"] = permissions_list

        return user_info

    def get_user_info(self, user_id: int) -> Dict[str, Any]:
        """
        Query and return user information by user_id, including the role ID.

        Args:
            user_id (int): The user ID to query.

        Returns:
            Dict[str, Any]: The user data if found and active.

        Raises:
            CustomException: If the user is not found or is disabled.
        """
        stmt = select(
            UserModel.user_id,
            UserModel.username,
            RoleModel.role_name
        ).join(
            RoleModel,
            RoleModel.role_id == UserModel.role_id
        ).where(
            UserModel.user_id == user_id,
            UserModel.active == ACTIVE,
            RoleModel.active == ACTIVE
        )

        user_info = self.db.query(stmt).first()

        if user_info:
            return user_info.as_dict()
        else:
            raise CustomException(
                f"Usuario {user_id} deshabilitado.", FORBIDDEN_STATUS
            )

    def get_role_permissions(self, role_id: int) -> list:
        """
        Retrieve the list of permissions associated with a given role.

        Args:
            role_id (int): The role ID to query for permissions.

        Returns:
            list: List of permission names associated with the role.
        """
        stmt = select(
            RolePermissionModel.permission_id,
            PermissionModel.permission_name
        ).join(
            PermissionModel,
            RolePermissionModel.permission_id ==
            PermissionModel.permission_id
        ).where(
            RolePermissionModel.role_id == role_id,
            RolePermissionModel.active == ACTIVE,
            PermissionModel.active == ACTIVE
        )

        permissions = self.db.query(stmt).all()

        return [perm.permission_name for perm in permissions]
