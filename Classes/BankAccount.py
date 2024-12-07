from typing import Any, Dict
from sqlalchemy import select, and_
from Models.AccountType import AccountTypeModel
from Models.Bank import BankModel
from Models.BankAccount import BankAccountModel
from Models.User import UserModel
from Utils.Constants import (
    ACTIVE,
    # INACTIVE,
    SUCCESS_STATUS,
    # CREATED_STATUS,
    # ERROR_STATUS,
    NO_DATA_STATUS,
)
from Utils.ExceptionsTools import CustomException
# from Utils.GeneralTools import get_input_data
from Utils.Response import _response
from Utils.Validations import Validations


class BankAccount:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)

    def get_bank_account(self, event: Dict[str, Any]) -> Dict[str, Any]:
        user_id = event.get("user_id")

        if not user_id:
            raise CustomException("No se proporcionó el ID del usuario.")

        self.validations.records(
            conn=self.db,
            model=UserModel,
            pk=user_id,
            error_class=CustomException(
                "No se encontró el usuario.", NO_DATA_STATUS
            ),
            as_dict=True,
        )

        stmt = (
            select(
                BankAccountModel,
                BankModel.bank_name,
                AccountTypeModel.account_type,
            )
            .join(
                BankModel,
                and_(
                    BankAccountModel.bank_id == BankModel.bank_id,
                    BankModel.active == ACTIVE,
                ),
            )
            .join(
                AccountTypeModel,
                and_(
                    BankAccountModel.account_type_id ==
                    AccountTypeModel.account_type_id,
                    AccountTypeModel.active == ACTIVE,
                ),
            )
            .join(
                UserModel,
                and_(
                    BankAccountModel.user_id == UserModel.user_id,
                    UserModel.active == ACTIVE
                )
            )
            .where(
                BankAccountModel.active == ACTIVE,
                BankAccountModel.user_id == user_id
            )
        )
        bank_accounts = self.db.query(stmt)

        return (
            _response(bank_accounts.as_dict(), SUCCESS_STATUS)
            if bank_accounts
            else _response({}, NO_DATA_STATUS)
        )
