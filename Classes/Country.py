from typing import Any, Dict
from sqlalchemy import select
from Models.Country import CountryModel
from Utils.Constants import (
    ACTIVE,
    SUCCESS_STATUS,
    NO_DATA_STATUS,
)
from Utils.GeneralTools import get_input_data


class Country:
    def __init__(self, db):
        self.db = db

    def get_countries(self, event: Dict[str, Any]) -> Dict[str, Any]:
        conditions = {"active": ACTIVE, **get_input_data(event)}
        conditions = {k: v for k, v in conditions.items() if v is not None}

        countries = self.db.query(
            select(CountryModel).filter_by(**conditions)
        ).as_dict()

        return {
            "statusCode": SUCCESS_STATUS if countries else NO_DATA_STATUS,
            "data": countries or "No se encontraron departamentos.",
        }
