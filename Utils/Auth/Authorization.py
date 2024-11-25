from sqlalchemy import select
from Models.User import UserModel
from Utils.ExceptionsTools import CustomException


class TokenTools:
    """
    Main class for token extraction data
    """

    def __init__(self, db):
        """Initializing class base attributes"""
        self.db = db
        self.token = {}

    @staticmethod
    def extract_token(event):
        token = {}
        # Extracting token authorizer data from lambda event
        if type(event) is dict:
            token = event["headers"]["Authorization"]
        return token

    def extract_user_info(self, event):
        user_id = event.get("user_id", 0)

        # Querying user data
        stmt = select(
            UserModel.user_id,
            UserModel.username,
            UserModel.fullname
        ).filter_by(user_id=user_id, active=1)
        user_info = self.db.query(stmt).first().as_dict()

        if user_info:
            username = user_info.get("username", "")
        else:
            # raise exception when user is disabled
            raise CustomException(f"User {username} is disable.", 403)

        return user_info
