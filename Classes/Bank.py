from typing import Any, Dict
from sqlalchemy import insert, select, update
from Models.Bank import BankModel
from Utils.Constants import (
    ACTIVE,
    INACTIVE,
    SUCCESS_STATUS,
    CREATED_STATUS,
    ERROR_STATUS,
    NO_DATA_STATUS,
)
from Utils.ExceptionsTools import CustomException
from Utils.GeneralTools import get_input_data
from Utils.Response import _response
from Utils.Validations import Validations


class Bank:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)
        self.fields = {}

    def list_banks(self, event: Dict[str, Any]) -> Dict[str, Any]:
        conditions = {"active": ACTIVE, **get_input_data(event)}

        banks = self.db.query(
            select(BankModel).filter_by(**conditions)
        )
        return (
            _response(banks.as_dict(), SUCCESS_STATUS)
            if banks
            else _response(None, NO_DATA_STATUS)
        )

    def add_bank(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)

        self.validations.validate_data(request, self.fields)

        bank_id = self.db.add(
            insert(BankModel).values(
                bank_name=request.get("bank_name")
            )
        )

        return (
            _response({"bank_id": bank_id}, CREATED_STATUS)
            if bank_id
            else _response(None, ERROR_STATUS)
        )

    def update_bank(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        bank_id = request.get("bank_id")

        self.validations.validate_data(request, self.fields, is_update=True)

        self.validations.records(
            conn=self.db,
            model=BankModel,
            pk=bank_id,
            error_class=CustomException("Bank not found.", NO_DATA_STATUS),
            as_dict=True,
        )

        is_updated = self.db.update(
            update(BankModel)
            .where(
                BankModel.bank_id == bank_id,
                BankModel.active == ACTIVE,
            )
            .values(bank_name=request.get("bank_name"))
        )

        return (
            _response({"is_updated": is_updated}, SUCCESS_STATUS)
            if is_updated
            else _response(None, ERROR_STATUS)
        )

    def delete_bank(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        bank_id = request.get("bank_id")

        self.validations.records(
            conn=self.db,
            model=BankModel,
            pk=bank_id,
            error_class=CustomException("Bank not found.", NO_DATA_STATUS),
            as_dict=True,
        )

        is_deleted = self.db.update(
            update(BankModel)
            .where(
                BankModel.bank_id == bank_id,
                BankModel.active == ACTIVE,
            )
            .values(active=INACTIVE)
        )

        return (
            _response({"is_deleted": is_deleted}, SUCCESS_STATUS)
            if is_deleted
            else _response(None, ERROR_STATUS)
        )
