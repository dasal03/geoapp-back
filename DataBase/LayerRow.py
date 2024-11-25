from datetime import datetime, date
from decimal import Decimal
from typing import Union
from collections.abc import Iterable


PARSE = {datetime: str, date: str, Decimal: float}


class LayerRow:
    parse: dict = PARSE

    def __init__(self, data: Union[dict, None] = None):
        """Constructor defined for the instance of class."""
        self._data = {}
        if type(data) is dict:
            self.__dict__.update(data)
            self._data = data

    def as_dict(self) -> dict:
        """Method returned the single record as dict."""
        for k, v in self._data.items():
            if type(v) in list(self.parse.keys()):
                self._data[k] = self.parse[type(v)](v)
        return self._data

    def __bool__(self) -> bool:
        """Magic method when instance call as bool object."""
        return len(self._data) > 0

    def __iter__(self) -> Iterable:
        """Magic method when instance call as iterable object."""
        return iter(self.as_dict().items())

    def __repr__(self) -> str:
        """Magic method when instance call as str object."""
        return str(self._data)
