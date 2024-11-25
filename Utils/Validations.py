from Utils.GeneralTools import (
    as_list,
    get_post_data,
    get_http_path_method,
    who_i_am_function,
)
from sqlalchemy import select
from re import (
    match as re_match,
    fullmatch as re_fullmatch,
    compile as re_compile,
    IGNORECASE as re_IGNORECASE,
)
from base64 import decodebytes as base64_decodebytes
from Utils.QueryTools import get_pk_name
from Utils.CalculationTools import str_to_date, str_to_datetime
from typepy import (
    Integer as tp_Integer,
    RealNumber as tp_RealNumber,
    Bool as tp_Bool,
    String as tp_String,
    List as tp_List,
)
from typing import List, Dict, Union, Tuple

DATE_TYPE = "date"
DATETIME_TYPE = "datetime"
EMAIL_TYPE = "email"


class Validations:

    CUSTOM_TYPES = (DATE_TYPE, DATETIME_TYPE, EMAIL_TYPE)
    CAST_TYPES = {
        int: {"type": tp_Integer, "strict_level": 1},
        float: {"type": tp_RealNumber, "strict_level": 0},
        str: {"type": tp_String, "strict_level": 1},
        bool: {"type": tp_Bool, "strict_level": 1},
        list: {"type": tp_List, "strict_level": 1},
    }

    def __init__(self, db):
        self.db = db

    @classmethod
    def validate(cls, array, cast: bool = True):
        """Validates provided parameters checking for empty values, value type
        and value length
        Args:
            array: The parameter array. Recommended: build with param method
            cast: If true values are tried to cast. Commonly used for lambda
            event query string parameters
        Returns:
            A dictionary with structure {isValid, data}
        """
        valid = True
        data = []
        reason = ""

        # Para cada parámetro a validar
        for param in array:
            # Obtener atributos
            data_value = param["value"]
            expected_type = param["type"]
            max_len: int = param.get("max_len", None)
            strict_level = param.get("strict_level", None)
            max_digits = param.get("max_digits", 0)
            min_len = param.get("min_len", None)
            greater_than_equal = param.get("ge", None)

            if data_value == "":  # Comprobando que no sea un valor vacío
                valid = False
                reason = f"vacío-{param['name']}"
                data.append(
                    f"* La clave '{param['name']}' "
                    f"no puede estar vacía."
                )

            # Comprobando tipo de dato
            elif not cls.check_data_type(
                    data_value, expected_type, cast, strict_level):
                valid = False
                reason = f"inválido-{param['name']}"
                data.append(
                    f"El valor de la clave '{param['name']}' "
                    f"debe ser {expected_type},"
                    f" no {type(data_value)}."
                )

            # Comprobando longitud máxima de datos
            elif max_len and not cls.check_data_length(
                    len(str(data_value)), max_len):
                valid = False
                reason = f"longitud-{param['name']}"
                data.append(
                    f"El valor de la clave '{param['name']}' "
                    f"debe tener una longitud de "
                    f"{max_len} o menor."
                )

            # Comprobando valor negativo
            elif (
                greater_than_equal is not None
            ) and not cls.is_greater_than_or_equal(
                value=data_value, limit=greater_than_equal,
                expected_type=expected_type
            ):
                valid = False
                reason = f"negativo-{param['name']}"
                data.append(
                    f"El valor de la clave '{param['name']}' "
                    f"debe ser {expected_type} "
                    "positivo."
                )

            # Comprobando longitud mínima de datos
            elif min_len and not cls.check_min_len(
                data=data_value,
                min_len=min_len,
                expected_type=param["type"],
            ):
                valid = False
                reason = f"min_longitud-{param['name']}"
                data.append(
                    f"El valor de la clave '{param['name']}' "
                    f"debe tener una longitud de "
                    f"{min_len} o mayor."
                )

            # Comprobando dígitos máximos
            elif max_digits and not cls.check_digit(
                data_digit=data_value,
                max_digits=max_digits,
                expected_type=param["type"],
            ):
                valid = False
                reason = f"max_dígito-{param['name']}"
                data.append(
                    f"El valor de la clave '{param['name']}' "
                    f"debe tener un máximo de {max_digits} "
                    f"dígitos o menos."
                )

        return {"isValid": valid, "data": data, "reason": reason}

    @classmethod
    def check_data_type(
        cls, data_value, expected_type,
        cast: bool = False, strict_level: int = None
    ) -> bool:
        """
        Checks if data value type matches expected type
        :param data_value:
        :param expected_type:
        :param cast: If true tries to convert data_value in expected_type
        :param strict_level: If cast is set to True, this is the strict level
        cast will use
        :return: bool
        """

        # Checking if is a custom type validation
        if expected_type in cls.CUSTOM_TYPES:
            # Defining custom validations methods
            custom_val = {
                DATE_TYPE: cls.validate_date,
                EMAIL_TYPE: cls.validate_email,
                DATETIME_TYPE: cls.validate_datetime,
            }
            # Executing custom validation method
            check_result = custom_val[expected_type](data_value)

        else:
            if cast:  # If cast is set True
                # Check if type is defined in CAST_TYPES
                type_ = cls.CAST_TYPES.get(expected_type, None)

                if type_ is None:
                    # To avoid future errors
                    check_result = type(data_value) is expected_type
                    # raise ValueError(f"Type {expected_type} cast is not "
                    #                  f"supported")
                else:

                    if strict_level is None:
                        strict_level = type_["strict_level"]

                    # Trying to cast
                    try_result = type_["type"](
                        data_value, strict_level=strict_level
                    ).try_convert()
                    check_result = False if try_result is None else True

            else:
                check_result = type(data_value) is expected_type

        return check_result

    @staticmethod
    def check_data_length(data_len: int, max_len: int) -> bool:
        """Compares the provided values to check if both are equal

        Args:
            data_len(int):
            max_len(int):

        Returns:
            bool: A boolean indicating whether the length is valid or not
        """
        return data_len <= max_len

    @staticmethod
    def is_greater_than_or_equal(
        value: int, limit: int, expected_type: any
    ) -> bool:
        """
        Return True if the value is greater than or equal to the limit,
        otherwise returnFalse.

        The function takes three arguments:

        - value: The value to compare.
        - limit: The value to compare against.
        - expected_type: The type of the value

        :param value: The value to be checked
        :type value: int
        :param limit: The limit to compare the value against
        :type limit: int
        :param expected_type: The type of the value that is being checked
        :type expected_type: any
        :return: A boolean value.
        """
        result = True

        if expected_type in [int, float]:
            result = value >= limit

        return result

    @staticmethod
    def check_digit(
        data_digit: int, max_digits: int, expected_type: any
    ) -> bool:
        """Compares the provided values to check if
            if the data is greater than the length
        Args:
            data_digit(int):
            max_digits(int):
            expected_type(any):
        Returns:
            bool: A boolean indicating whether the length is valid or not
        """
        result = False
        if type(data_digit) == expected_type and expected_type in [int, float]:

            data_digit = str(data_digit)
            split_data_digit = data_digit.split(".")
            data_digit = len(split_data_digit[0])

            result = data_digit <= max_digits

        return result

    @staticmethod
    def check_min_len(data: int, min_len: int, expected_type: any) -> bool:
        """check if data if greater or equal than min len

        Args:
            data(int):
            min_len(int):
            expected_type(any):
        Returns:
            bool: A boolean indicating whether the length is valid or not
        """
        result = False
        if type(data) == expected_type and expected_type in [int, str]:
            data = len(str(data).strip())
            result = data >= min_len

        return result

    @staticmethod
    def param(
        name,
        type,
        value,
        max_len: int = None,
        min_len: int = None,
        strict_level: int = None,
        max_digits: int = 0,
        ge: Union[int, float] = None,
    ) -> dict:
        """Builds param dictionary to use with validate method"""
        return {
            "name": name,
            "type": type,
            "value": value,
            "max_len": max_len,
            "strict_level": strict_level,
            "max_digits": max_digits,
            "min_len": min_len,
            "ge": ge,
        }

    @classmethod
    def records(
        cls,
        conn,
        model,
        pk: int or list,
        pk_name: str = None,
        column_active_name="active",
        column_active_value=1,
        error_class=KeyError,
        as_dict=False,
        **aditional_filter,
    ) -> list:
        """Validate a record of any model, passing the pk value (support
        list of values) and pk_name is got of model and especified the
        connection to DB.

        Args:
            - conn (DBConnect): connection to DB. eg: `self.db.read_session`
            - model (DBBase): Model. eg: `LoanModel`
            - pk (int or list): value of pk of model (suppor list)
                eg: `1 or [1, 2, 3]`
            - pk_name (str): name of pk of model if not specified is get
                             of model.
                eg: `'loan_id'`
            - column_active_name (str, optional): in case model use `deleted`.
                eg: `'deleted'`
                Defaults to 'active'.
            - column_active_value (int, optional): in case model use `deleted`.
                eg: `0`
                Defaults to 1.
            - error_class (Exception): Error clas to raise in case not pass
                                       validation
                eg: `AssertionError`
                Defaults to KeyError but should be AssertionError
            - as_dict (bool): apply as_dict method in the return data
                eg: `AssertionError`
                Defaults to KeyError but should be AssertionError

        Raises:
            KeyError: for compatibility and by defaults to error_class
                      argument, but this should be `AssertionError`.

        Return:
            (list[<LayerRow>, ...] `or if as_dict=True` -> list[{..}, ...]):
            the object returning in a query execution or if arg as_dict is
            True return a list of dict, you can apply the `as_dict` method
            to each item in case as_dict is False.
        """
        pk_list = as_list(pk)
        records = []
        for pk in pk_list:
            # Querying by primary key
            record = conn.query(
                select(model).filter_by(
                    **{
                        pk_name or get_pk_name(model): pk,
                        column_active_name: column_active_value,
                    },
                    **aditional_filter,
                )
            ).first()
            if not record:  # If not found raise error
                raise error_class
            records.append(record.as_dict() if as_dict else record)
        return records

    def processFile(
        self,
        file_list: List[Dict[str, str]],
        extensions: list = None,
        max_size: int = 2097152,
    ) -> None:
        """Checks file extension and max size

        Args:
            file_list: A list with files to validate in base64 string format.
                Each item must have keys filename and file(base64)
            extensions: A list with allowed extension
            max_size: The allowed maximum size per file

        Returns:
            Void

        Raises:
            KeyError: If:
                - extension is not allowed
                - file exceeds maximum size
                - file or filename is empty
        """
        for item in file_list:
            # get file extension available
            if extensions is None:  # Find default allowed extensions
                extensions = [
                    "gif",
                    "jpg",
                    "jpeg",
                    "docx",
                    "xlsx",
                    "xls",
                    "csv",
                    "crt",
                    "gif",
                    "txt",
                    "pdf",
                    "html",
                ]
                extensions = [e.description for e in extensions]

            # validate file params
            if not len(item["filename"]) or not len(item["file"]):
                raise KeyError("Item filename or file key is empty")

            split_name = item["filename"].split(".")
            extension = split_name.pop()

            if not any(e == extension.lower() for e in extensions):
                raise KeyError("File extension is not allowed")

            # convert to byte
            file_base64 = item["file"].encode("utf-8")
            decode_file_data = base64_decodebytes(file_base64)

            # check size file
            if len(decode_file_data) > max_size:
                raise KeyError("File exceeds maximum allowed size")

    @staticmethod
    def alpha_space(param: str):
        """Checks param is alphanumeric containing spaces or middle dashes"""
        _str = r"^[a-zA-Z0-9][a-zA-Z0-9\.\- ]{0,255}[a-zA-Z0-9]$"
        return True if re_fullmatch(_str, param.rstrip()) else False

    @staticmethod
    def is_url(param: str):
        """Checks param is a valid url"""
        regex = re_compile(
            r"^(?:http|ftp)s?://"  # http:// or https://
            # domain...
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|"
            r"[A-Z0-9-]{2,}\.?)|"
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re_IGNORECASE,
        )

        return True if re_match(regex, param) else False

    @staticmethod
    def validate_email(email: str) -> bool:
        """Checks email is a valid email"""
        __email = r"^[^\.@\s][^@\s]*?([^\.@\s]@(?!\.))"
        __email += r"{1}([^@\s]+([.][a-zA-Z0-9]{1,}){1,}){1}$"
        try:
            resp = True if re_fullmatch(__email, email) else False
        except Exception:
            resp = False
        return resp

    @staticmethod
    def validate_date(date, type_: str = DATE_TYPE) -> bool:
        """Validates date has a date or datetime data type depending on
        provided type_"""
        result = True

        try:
            if type_ == DATE_TYPE:
                str_to_date(date)
            elif type_ == DATETIME_TYPE:
                str_to_datetime(date)
        except ValueError:
            result = False

        return result

    @classmethod
    def validate_datetime(cls, date):
        """Validates date is a datetime str or object"""
        return cls.validate_date(date, DATETIME_TYPE)

    @staticmethod
    def is_float(num):
        """Checks if num is or can be a float"""
        try:
            float(num)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_numeric(value: str or list):
        """
        validate if the character is numeric and not zero
        Args:
            - value(str, optional): one string or list or strings.
        Raises:
            ValueError: for compatibility, but this should be `AssertionError`
        """
        for one_value in as_list(value):
            type_value = type(one_value)
            if type_value is str:
                if not str(one_value).isnumeric():
                    raise ValueError("Invalid number supplied")
            elif type_value is int or type_value is float:
                if int(one_value) < 0:
                    raise ValueError("Number supplied is less than zero")

    @staticmethod
    def pop_many(dictionary: dict, items: list) -> dict:
        """delete a multiple key, value from dict"""

        for item in items:
            dictionary.pop(item)

        return dictionary

    @staticmethod
    def pop_exclude(dictionary: dict, items: list) -> dict:
        """delete a multiple key, value from dict excluding all in params"""
        return {k: v for k, v in dictionary.items() if k in items}

    @classmethod
    def validate_multiple_required(
        cls, data: dict, data_val: list, strict_level: int = None
    ) -> list:
        """
        Validate that the required data set exists.
        Args:
            data (dict): Dictionary to get data.
            data_val (list): List of key to validate and get.
            Example:
                [{key_name: str, type: typeClass, value: any,
                  max_len: int = None,strict_level: None}]
            strict_level (int, optional): Set the strict level to cast.
        Returns:
            list: A list of dictionary valitation params.
        """
        data_save: list = []

        for val in data_val:
            cls.add_validate_field(
                data_save,
                data,
                val["key"],
                val["type"],
                val.get("len"),
                True,
                strict_level,
            )

        return data_save

    @classmethod
    def validate_multiple_optional(
        cls, data_save: list, data: dict,
        data_val: list, strict_level: int = None
    ) -> None:
        """
        Add optional data of  valitation params to the dictionary if exist.
        Args:
            data_save (list): List to save the data.
            data (dict): Dictionary to get data.
            Example:
                [{key_name: str, type: typeClass, value: any,
                  max_len: int = None,strict_level: None}]
            data_val (list): List of key to validate and get.
            strict_level (int, optional): Set the strict level to cast.
        """
        for val in data_val:
            cls.add_validate_field(
                data_save,
                data,
                val["key"],
                val["type"],
                val.get("len"),
                strict_level=strict_level,
            )

    @classmethod
    def add_validate_field(
        cls,
        list_vals: list,
        data: dict,
        key: str,
        type_data: type,
        max_len: int = None,
        required: bool = False,
        strict_level: int = None,
    ) -> None:
        """
        Validates if the key exists in the data dictionary
        and adds it to the list of validations.
        Args:
            list_vals (list): The list of validations
            data (dict): The dictionary of data payload
            key (str): The key to validate
            type_data (type): The type of data
            max_len (int, optional): The max lenght if is string.
            required (bool, optional): Activate the required error.
            strict_level (int, optional): Set the strict level to cast.
        """
        if data.get(key, None) is not None:
            list_vals.append(
                cls.param(key, type_data, data[key], max_len, strict_level)
            )
        elif required:
            raise KeyError(f"Required param '{key}' not found.")


def check_query_limit(
    limit: Union[int, str] = 0, offset: Union[int, str] = 0, cast: bool = True
) -> Tuple[int, int]:
    """
    Validates limit parameters are int type
    Args:
        limit:
        offset:
        cast:
    Returns:
        A tuple with values as integers
    """
    # Checking data types
    val_result = Validations.validate(
        [
            Validations.param("limit", int, limit),
            Validations.param("offset", int, offset),
        ],
        cast=cast,
    )
    assert val_result["isValid"]
    return int(limit), int(offset)


def validate_nit(nit: str):
    """
    Validate nit is correct.
    ref: https://es.wikipedia.org/wiki/
    N%C3%BAmero_de_Identificaci%C3%B3n_Tributaria
    """
    nit = nit.strip()

    if not bool(nit):
        return False

    if len(nit) != 10:
        return False

    mult = [41, 37, 29, 23, 19, 17, 13, 7, 3]  # multiplicadores
    v = sum(list(map(lambda x, y: x * y, mult, [int(c) for c in nit[:-1]])))
    v = int(v) % 11

    if v >= 2:
        v = 11 - v

    return str(v) == nit[9]


def eval_bool(data: any, key_name: str = "") -> bool:
    """Checks if data is bool type by evaluating it if a str is provided"""
    message = f"Parameter {key_name} must be true or false"

    if type(data) is str:
        try:
            data = eval(data)
        except NameError:
            pass

    assert type(data) is bool, message
    return data


# LEGACY: references from this module
# for future use Utils.GeneralTools.<function>
get_post_data = get_post_data
get_http_path_method = get_http_path_method
who_i_am_function = who_i_am_function
