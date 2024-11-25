import decimal
import datetime
from sqlalchemy.orm.decl_api import DeclarativeMeta
from typing import Union, List

"""please dear developer, do not place imports to your own
modules that are not in the default modules, nor create
classes here, only independent and consistent functions.
remember to add their respective DocString if your function
is complex ;)."""

MODEL_PYTHON_CAST = {
    "INTEGER": int,
    "BIGINT": int,
    "DATE": "date",
    "DATETIME": "datetime",
    "NUMERIC": float,
    "TEXT": str,
    "VARCHAR": str,
}

MODEL_MYSQL_CAST = {"NUMERIC": "DECIMAL", "INTEGER": "INT"}


def get_model_columns(
    model,
    exclude_primary: bool = False,
    exclude_defaults: bool = True,
    get_attributes: bool = False,
    excluded_columns=[],
) -> Union[list, dict]:
    """
    Returns a list of column names as strings
    :param model:
    :param exclude_primary: Decides whether to exclude table primary_key
    :param exclude_defaults: Decides whether to exclude active and timestamp
    columns
    :param get_attributes: If True a dictionary with column: attributes
    structure is returned
    :param excluded_columns: list of column names(string) to exclude
    :return: list of column names as strings
    """
    model_columns = model.__table__.columns  # Get all model columns
    table_name = model.__tablename__  # Get table name
    column_names = {} if get_attributes else []

    if exclude_defaults:
        # Extending excluded columns
        excluded_columns.extend(
            ["active", "deleted", "created_at", "updated_at"]
        )

    for col in model_columns:
        # Getting column name
        column_name = str(col).replace(f"{table_name}.", "")

        if column_name in excluded_columns:
            continue

        if exclude_primary and col.primary_key:  # Exclude primary key
            continue

        if get_attributes:
            # Getting each column attributes
            column_names.update(**{column_name: get_column_attributes(col)})
        else:
            column_names.append(column_name)

    return column_names


def all_columns_excluding(
    model, excluded: list = None, primary_key=False
) -> list:
    """
    Build the columns for select excluding the specified fields
    Use example:
    stmt = select(all_columns_excluding(LoanModel, 'loan_id'))
    :param primary_key: Excludes primary key
    :param model:
    :param excluded: A list of fields to exclude
    :return: list of columns
    """
    if excluded is None:
        excluded = []

    column_list = []

    for col in model.__table__.columns:  # For each model column

        if primary_key and col.primary_key:  # Exclude primary key
            excluded.append(col.key)

        if col.key not in excluded:  # Exclude indicated keys
            column_list.append(col)

    return column_list


def generate_cast_type_model(
    model,
    exclude_primary: bool = True,
    exclude_defaults: bool = True,
    excluded_columns=[],
) -> dict:
    """Generates cast type model columns' dictionary with structure
    {model_column_name: type}
    Args:
        model:
        exclude_primary: Decides whether to exclude table primary_key
        exclude_defaults:  Decides whether to exclude active and timestamp
            columns
        excluded_columns: A list of column names(as string) to exclude
    Returns:
    """
    # Getting table columns and name
    model_columns = model.__table__.columns
    table_name = model.__tablename__
    column_names = {}

    if exclude_defaults:
        # Extending excluded columns
        excluded_columns.extend(
            ["active", "deleted", "created_at", "updated_at"]
        )

    for col in model_columns:

        # Getting column name
        column_name = str(col).replace(f"{table_name}.", "")

        if column_name in excluded_columns:
            continue

        if exclude_primary and col.primary_key:  # Excluding primary key
            continue

        # Extracting and casting column type
        text_type = type_to_str(col.type)
        type_ = cast_type(text_type)
        column_names[column_name] = type_

    return column_names


def generate_json_model(model, cal_index=True):
    """Generates a JSON including all model properties
    Args:
        model:
        cal_index:
    Returns:
        A dictionary with structure {table, rows, indexes}
    """
    table_name = model.__tablename__
    # Getting all columns and their attributes
    column_names = get_model_columns(model, False, False, True)
    indexes = set()
    rows = {}

    for name_col, column in column_names.items():
        clean_row = {}
        type_ = column.pop("type_str", "VARCHAR")
        default = column.pop("server_default", None)
        # Getting column default values
        if default:
            column["default"] = default

        if column["default"] == (
            "CURRENT_TIMESTAMP" and name_col.find("ted_at") > -1
        ):
            type_ = "TIMESTAMP"

        # Getting column type
        column["type"] = (
            MODEL_MYSQL_CAST[type_] if type_ in MODEL_MYSQL_CAST else type_)

        for name_attr, attr in column.items():  # Getting model indexes
            if name_attr == "index" and attr:
                indexes.add(name_col)
                continue
            elif name_attr == "primary" and not attr:
                if name_col.find("_id") > -1 and cal_index:
                    indexes.add(name_col)

            if attr:
                clean_row[name_attr] = attr

        if name_col == "active":
            indexes.add(name_col)

        rows[name_col] = clean_row

    return {"table": table_name, "rows": rows, "indexes": list(indexes)}


def get_others_id_columns(model: DeclarativeMeta) -> list:
    return [
        column.endswith("_id")
        for column in get_model_columns(model, exclude_primary=True)
    ]


def get_pk_name(model: DeclarativeMeta) -> str:
    """Gets primary key model column name"""
    return model.__table__.primary_key.columns.values()[0].name


def dumps_default(obj):
    """Function used for json dumps default object conversion"""
    if isinstance(obj, decimal.Decimal):  # Decimal type
        return float(obj)
    elif isinstance(obj, datetime.date):  # Date type
        return str(obj)
    else:
        return obj


def print_query(stmt):
    """Function used to print orm + pymysql output query"""
    from DataBase.DataBase import DataBase

    sql = DataBase.compile_sql(stmt, ())
    output = sql[0] % sql[1]
    print(output, ";")
    return output


def cast_type(type_: str) -> Union[object, str]:
    """
    Cast string to class/custom type
    :param type_:
    :return: Type to be used with validate method from Validations class
    :raises ValueError: if type_ is not a string
    """
    if type(type_) is not str:
        raise ValueError("Provided type must be a string")

    type_ = type_to_str(type_)

    return (
        MODEL_PYTHON_CAST[type_] if
        MODEL_PYTHON_CAST.get(type_, "") else type_
    )


def type_to_str(type_):
    """Strip parenthesis and return db type"""
    return str(type_).split("(", 1)[0]


def get_column_attributes(column):
    """Get provided sqlalchemy model column attributes"""
    # Extracting type
    raw_type = column.type
    text_type = type_to_str(raw_type)
    type_ = cast_type(text_type)

    length = ""

    # Extracting default values
    default = str(column.default.arg) if column.default else column.default
    server_default = (
        str(column.server_default.arg)
        if column.server_default
        else column.server_default
    )
    on_update = (
        str(column.onupdate.arg) if column.onupdate else column.onupdate)

    # Extracting length
    if text_type in ["VARCHAR"]:
        length = raw_type.length if getattr(raw_type, "length") else 255
    elif text_type in ["NUMERIC"]:
        length = (
            f"{raw_type.precision},{raw_type.scale}"
            if getattr(raw_type, "precision")
            else "18,2"
        )

    return {
        "primary": 1 if column.primary_key else 0,
        "type": type_,
        "type_str": text_type,
        "length": length,
        "nullable": "NULL" if column.nullable else "NOT NULL",
        "server_default": server_default,
        "default": default,
        "on_update": on_update,
        "index": column.index,
    }


def select_columns(model, columns_list: List[str]) -> list:
    return [getattr(model, col_name) for col_name in columns_list]
