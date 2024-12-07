from typing import Any, Dict
from sqlalchemy import select
from Models.City import CityModel
from Models.State import StateModel
from Utils.Constants import (
    ACTIVE,
    # INACTIVE,
    SUCCESS_STATUS,
    # CREATED_STATUS,
    # ERROR_STATUS,
    NO_DATA_STATUS,
)
from Utils.ExceptionsTools import CustomException
from Utils.GeneralTools import get_input_data
from Utils.Response import _response
from Utils.Validations import Validations


class City:

    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)
        self.fields = {
            "city_name": str,
        }

    def get_cities(self, event: Dict[str, Any]):
        request = get_input_data(event)
        state_id = request.get("state_id")

        if not state_id:
            raise CustomException(
                "No se proporcionó el ID del estado.", NO_DATA_STATUS
            )

        self.validations.records(
            conn=self.db,
            model=StateModel,
            pk=state_id,
            error_class=CustomException(
                "No se encontró el estado.", NO_DATA_STATUS
            ),
            as_dict=True,
        )
        stmt = select(CityModel).where(
            CityModel.state_id == state_id,
            CityModel.active == ACTIVE
        )
        result = self.db.query(stmt)

        return (
            _response(result.as_dict(), SUCCESS_STATUS)
            if result
            else _response(None, NO_DATA_STATUS)
        )
