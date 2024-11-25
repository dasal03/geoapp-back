from datetime import datetime
from hashlib import sha256
from json import loads as json_loads
from copy import copy
from typing import Union, Tuple


"""please dear developer, do not place imports to your own
modules that are not in the default modules, nor create
classes here, only independent and consistent functions.
remember to add their respective DocString ;)."""


COLLECTION_LIST = [list, tuple, set]
COLLECTION_KEY_VALUE = [dict]
COLLECTION_TYPES = [*COLLECTION_LIST, *COLLECTION_KEY_VALUE]


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


def as_set(value: Union[list, set, any]) -> set:
    """as the name says, return the passing value as set."""
    return (
        set(value)
        if type(value)
        in (
            list,
            tuple,
            set,
        )
        else {value}
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


def try_load_json_column(data: Union[str, None]) -> Union[dict, any]:
    """Try loads str sospected is a JSON."""
    try:
        return json_loads(data) if type(data) is str else data
    except Exception:
        return data


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


def group_by_multiple_key(
    list_dict: list, keys: list or str, items_key_name: str = "data"
) -> list:
    """Group and aggregate a list of dictionaries by multiple keys."""
    from collections import OrderedDict

    d = OrderedDict()
    keys = as_list(keys)
    for dic in list_dict:
        compose_key = [dic.pop(key) for key in keys]
        d.setdefault(tuple(compose_key), list()).append(dic)
    return [
        {
            **({keys[i]: k[i] for i in range(len(keys))}),  # link compose_key
            items_key_name: v,  # assign items_key_name
        }
        for k, v in d.items()
    ]
