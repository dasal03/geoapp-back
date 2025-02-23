from typing import Any, Dict
from sqlalchemy import select
from Models.DocumentType import DocumentTypeModel
from Utils.Constants import (
    ACTIVE,
    SUCCESS_STATUS,
    NO_DATA_STATUS,
)
from Utils.GeneralTools import get_input_data


class DocumentType:
    def __init__(self, db):
        self.db = db

    def get_document_types(self, event: Dict[str, Any]) -> Dict[str, Any]:
        conditions = {"active": ACTIVE, **get_input_data(event)}
        conditions = {k: v for k, v in conditions.items() if v is not None}

        stmt = select(DocumentTypeModel).filter_by(**conditions)
        data = self.db.query(stmt).as_dict()

        return {
            "statusCode": SUCCESS_STATUS if data else NO_DATA_STATUS,
            "data": data or "No se encontraron tipos de documentos",
        }
