from typing import Any, Dict
from sqlalchemy import select
from Models.Gender import GenderModel
from Utils.Constants import (
    ACTIVE,
    # INACTIVE,
    SUCCESS_STATUS,
    # CREATED_STATUS,
    # ERROR_STATUS,
    NO_DATA_STATUS,
)

# from Utils.ExceptionsTools import CustomException
from Utils.GeneralTools import get_input_data
from Utils.Response import _response
from Utils.Validations import Validations


class Gender:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)
        self.fields = {
            "gender_name": str,
        }

    def get_genders(self, event: Dict[str, Any]) -> Dict[str, Any]:
        conditions = {"active": ACTIVE, **get_input_data(event)}
        stmt = select(GenderModel).filter_by(**conditions)
        result = self.db.query(stmt)

        return (
            _response(result.as_dict(), SUCCESS_STATUS)
            if result
            else _response(None, NO_DATA_STATUS)
        )
