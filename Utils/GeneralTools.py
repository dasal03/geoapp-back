import os
import resend
import bcrypt
from datetime import datetime
from hashlib import sha256
from json import loads as json_loads
from copy import copy
from typing import Union, Tuple


COLLECTION_LIST = [list, tuple, set]
COLLECTION_KEY_VALUE = [dict]
COLLECTION_TYPES = [*COLLECTION_LIST, *COLLECTION_KEY_VALUE]

resend.api_key = os.getenv("RESEND_API_KEY")


def as_list(value: Union[list, any]) -> list:
    """as the name says, return the passing value as list."""
    return (
        list(value)
        if type(value)
        in (
            list,
            tuple,
            set,
        )
        else [value]
    )


def generate_hash_from_date() -> str:
    """Generate SHA 256 with hexdigest."""
    return sha256(bytes(str(datetime.now()), "utf-8")).hexdigest()


def generate_hash_from_text(text: str) -> str:
    """Generate SHA 256 with hexdigest from text."""
    return sha256(bytes(text, "utf-8")).hexdigest()


def get_http_path_method(event: dict) -> Tuple[str, str]:
    """Get HTTP method from event."""
    if type(event) is dict:
        return event.get("path", ""), event.get("httpMethod", "")
    return None, None


def who_i_am_function(event: dict, context: dict) -> Tuple[str, str, str]:
    """Get from event and context values to identify event exceution."""
    path, method = get_http_path_method(event)
    assert method, "Error in get http method"
    name = context.function_name
    return name, path, method


def _get_input_data(event: dict, key: str) -> Union[dict, any]:
    """Internal method to get data from event"""
    data = {}
    if type(event) is dict and key in event.keys():
        data = copy(event[key])
        if not type(data) is dict:
            try:
                data = json_loads(data)
            except Exception:
                data = {}
    return data


def get_post_data(event: dict) -> Union[dict, any]:
    """
    return data from event body

    Methods:
        - POST
        - PUT
    """
    return _get_input_data(event, "body")


def get_querystringparameters_data(event: dict) -> Union[dict, any]:
    """
    return data from event queryStringParameter

    Methods:
        - GET
        - DELETE
    """
    return _get_input_data(event, "queryStringParameters")


def get_input_data(
    event: dict, default_http_method: str = "POST"
) -> Union[dict, any]:
    """
    return data from event pending of method

    Methods:
        - GET       event['queryStringParameters']
        - POST      event['body']
        - DELETE    event['queryStringParameters']
        - PUT       event['body']
    """
    input_type = {
        "GET": get_querystringparameters_data,
        "POST": get_post_data,
        "DELETE": get_querystringparameters_data,
        "PUT": get_post_data,
    }
    path, method = get_http_path_method(event)
    method = method or default_http_method
    assert method.upper() in input_type.keys(), "Method Http dont supported."
    return input_type[method.upper()](event)


def encrypt_field(password: str) -> str:
    """ Encrypt received password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def decrypt_password(password: str, encrypted_password: str) -> str:
    """ Decrypt encrypted password and compare with received."""
    return bcrypt.checkpw(password.encode(), encrypted_password.encode())


def send_mail(mail_data) -> dict:
    print(f"Sending email: {mail_data}")
    _from = mail_data["from"]
    _to = mail_data["_to"]
    _subject = mail_data["_subject"]
    _template = mail_data["_template"]

    r = resend.Emails.send(
        {
            "from": _from,
            "to": _to,
            "subject": _subject,
            "html": _template,
        }
    )
    print(f"Email sent: {r}")
    return r
