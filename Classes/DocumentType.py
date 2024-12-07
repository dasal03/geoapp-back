from typing import Any, Dict
from sqlalchemy import select
from Models.DocumentType import DocumentTypeModel
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


class DocumentType:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)
        self.fields = {
            "description": str,
            "abbreviation": str,
        }

    def get_document_types(self, event: Dict[str, Any]) -> Dict[str, Any]:
        request = get_input_data(event)
        conditions = {"active": ACTIVE, **request}

        stmt = select(DocumentTypeModel).filter_by(**conditions)

        data = self.db.query(stmt)

        return (
            _response(data.as_dict(), SUCCESS_STATUS)
            if data
            else _response({}, NO_DATA_STATUS)
        )
