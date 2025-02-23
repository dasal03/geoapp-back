from typing import Any, Dict
from sqlalchemy import select, insert, update, and_
from Models.Management import ManagementModel
# from Models.Location import LocationModel
from Models.MaintenanceStatus import MaintenanceStatusModel
from Models.MaintenanceStatusCab import MaintenanceStatusCabModel
from Utils.Constants import (
    ACTIVE,
    INACTIVE,
    CREATED_STATUS,
    SUCCESS_STATUS,
    ERROR_STATUS,
    NO_DATA_STATUS,
)
from Utils.ExceptionsTools import CustomException
from Utils.GeneralTools import get_input_data
from Utils.Response import _response
from Utils.Validations import Validations


class Management:
    fields = {
        "description": str,
        "serial": str,
        "model": str
    }
    valid_extensions = ["jpg", "jpeg", "png", "gif", "webp"]

    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)

    def get_managements(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        conditions = {"active": ACTIVE, **request}
        stmt = (
            select(ManagementModel)
            .filter_by(**conditions)
            .order_by(ManagementModel.management_id)
        )

        equipments = self.db.query(stmt)
        return (
            _response(equipments.as_dict(), SUCCESS_STATUS)
            if equipments
            else _response({}, NO_DATA_STATUS)
        )
