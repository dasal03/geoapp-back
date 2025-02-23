from typing import Any, Dict
from sqlalchemy import select
from Models.State import StateModel
from Utils.Constants import (
    ACTIVE,
    SUCCESS_STATUS,
    NO_DATA_STATUS,
)
from Utils.GeneralTools import get_input_data


class State:
    def __init__(self, db):
        self.db = db

    def get_states(self, event: Dict[str, Any]) -> Dict[str, Any]:
        conditions = {"active": ACTIVE, **get_input_data(event)}
        conditions = {k: v for k, v in conditions.items() if v is not None}

        states = self.db.query(
            select(StateModel).filter_by(**conditions)
        ).as_dict()

        return {
            "statusCode": SUCCESS_STATUS if states else NO_DATA_STATUS,
            "data": states or "No se encontraron departamentos.",
        }
