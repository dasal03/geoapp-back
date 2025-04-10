from typing import Any, Dict
# from sqlalchemy import insert, select, update
from Utils.Constants import (
    ACTIVE,
    INACTIVE,
    SUCCESS_STATUS,
    CREATED_STATUS,
    ERROR_STATUS,
    NO_DATA_STATUS,
)
from Utils.Validations import Validations
from Utils.GeneralTools import get_input_data, send_mail
# from Utils.ExceptionsTools import CustomException


class Contact:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)
        self.fields = {
            "name": str,
            "email": str,
            "message": str
        }

    def send_contact_msg(self, event: Dict[str, Any]):
        request = get_input_data(event)
        self.validations.validate_data(request, self.fields)

        # mail payload
        _subject = "Mensaje de prueba"
        mail_data = {
            "from": request.get("email"),
            "_to": "miguelan238@gmail.com",
            "_subject": _subject,
            "_template": f"""
                <p>Nombre: {request.get('name')}</p>
                <p>Email: {request.get('email')}</p>
                <p>Asunto: {_subject}</p>
                <p>Mensaje: {request.get('message')}</p>
            """
        }

        send_contact_msg = send_mail(mail_data)

        # Save trazability
        # stmt = insert(ContactUsModel).values(request)
        # self.db.add(stmt)

        return {"statusCode": CREATED_STATUS, "data": send_contact_msg}
