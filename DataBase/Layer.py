from DataBase.LayerRow import LayerRow
from typing import List


class Layer:
    """Class for represents set of records returned of a query."""

    def __init__(self, data):
        """Constructor defined for the instance of class."""
        self._data: List[LayerRow] = []

        if type(data) is dict:
            self._data.append(LayerRow(data))
        elif data is not None:
            for row in data:
                self._data.append(LayerRow(row))

    def all(self) -> List[LayerRow]:
        """Method dummy for return all records."""
        return self._data

    def first(self) -> LayerRow:
        """Method tor return only the first record."""
        return self._data[0] if len(self._data) > 0 else LayerRow()

    def as_dict(self) -> List[dict]:
        """Method returned all records as dicts."""
        ndata = []
        for data in self._data:
            ndata.append(data.as_dict())
        return ndata

    def __bool__(self) -> bool:
        """Magic method when instance call as bool object."""
        return len(self._data) > 0

    def __repr__(self) -> str:
        """Magic method when instance call as str object."""
        ndata = []
        for data in self._data:
            ndata.append(str(data))
        return str(ndata)

    # ALIASES
    __dict__ = as_dict
