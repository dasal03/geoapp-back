from typing import Any, Dict
from sqlalchemy import select
from Models.State import StateModel
from Utils.Constants import (
    ACTIVE,
    # INACTIVE,
    SUCCESS_STATUS,
    # CREATED_STATUS,
    # ERROR_STATUS,
    NO_DATA_STATUS,
)
# from Utils.ExceptionsTools import CustomException
# from Utils.GeneralTools import get_input_data
from Utils.Response import _response
from Utils.Validations import Validations


class State:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)
        self.fields = {"state_name": str}

    def get_states(self, event: Dict[str, Any]) -> Dict[str, Any]:

        stmt = select(StateModel).where(StateModel.active == ACTIVE)
        states = self.db.query(stmt)

        return (
            _response(states.as_dict(), SUCCESS_STATUS)
            if states
            else _response(None, NO_DATA_STATUS)
        )
