from typing import Any, Dict
from sqlalchemy import select
from Models.Bank import BankModel
from Utils.Constants import (
    ACTIVE,
    SUCCESS_STATUS,
    NO_DATA_STATUS,
)
from Utils.GeneralTools import get_input_data


class Bank:
    def __init__(self, db):
        self.db = db

    def get_banks(self, event: Dict[str, Any]) -> Dict[str, Any]:
        conditions = {"active": ACTIVE, **get_input_data(event)}
        conditions = {k: v for k, v in conditions.items() if v is not None}

        stmt = select(BankModel).filter_by(**conditions)
        banks = self.db.query(stmt).as_dict()

        return {
            "statusCode": SUCCESS_STATUS if banks else NO_DATA_STATUS,
            "data": banks or "No se encontraron bancos",
        }
