from typing import Any, Dict
from sqlalchemy import select
from Models.City import CityModel
from Utils.Constants import (
    ACTIVE,
    SUCCESS_STATUS,
    NO_DATA_STATUS,
)
from Utils.GeneralTools import get_input_data


class City:

    def __init__(self, db):
        self.db = db

    def get_cities(self, event: Dict[str, Any]):
        conditions = {"active": ACTIVE, **get_input_data(event)}
        conditions = {k: v for k, v in conditions.items() if v is not None}

        stmt = select(CityModel).filter_by(**conditions)
        result = self.db.query(stmt).as_dict()

        return {
            "statusCode": SUCCESS_STATUS if result else NO_DATA_STATUS,
            "data": result or "No se encontraron ciudades."
        }
