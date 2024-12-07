from __future__ import annotations
from typing_extensions import NotRequired
from typing import Union, TypedDict
from Utils.Http.StatusCode import StatusCode


class APIResponseType(TypedDict):

    statusCode: Union[int, StatusCode]
    data: Union[dict, list, str, any]
    exception: NotRequired[dict | None]


class ValidateType(TypedDict):
    isValid: bool
    data: list[str]
