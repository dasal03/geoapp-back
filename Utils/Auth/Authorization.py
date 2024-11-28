from typing import Dict, Any
from sqlalchemy import select
from Models.User import UserModel
from Utils.Constants import ACTIVE, FORBIDDEN_STATUS
from Utils.ExceptionsTools import CustomException
from Utils.QueryTools import all_columns_excluding


class TokenTools:
    """
    Main class for token extraction data
    """

    def __init__(self, db):
        """Initializing class base attributes"""
        self.db = db
        self.token = {}

    @staticmethod
    def extract_token(event: Dict[str, Any]) -> Dict[str, Any]:
        token = {}
        # Extracting token authorizer data from lambda event
        if type(event) is dict:
            token = event["headers"]["Authorization"]
        return token

    def extract_user_info(self, event: Dict[str, Any]) -> Dict[str, Any]:
        user_id = event.get("user_id", 0)

        # Querying user data
        stmt = select(
            *all_columns_excluding(UserModel, "password")
        ).filter_by(user_id=user_id, active=ACTIVE)
        user_info = self.db.query(stmt).first().as_dict()

        if user_info:
            username = user_info.get("username", "")
        else:
            # raise exception when user is disabled
            raise CustomException(
                f"Usuario {username} desabilitado.", FORBIDDEN_STATUS
            )

        return user_info
