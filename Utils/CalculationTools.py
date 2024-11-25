from datetime import datetime, date
from calendar import isleap, monthrange
from operator import add as operator_add
from functools import reduce
from decimal import Decimal

"""please dear developer, do not place imports to your own
modules that are not in the default modules, nor create
classes here, only independent and consistent functions.
remember to add their respective DocString if your function
is complex ;)."""


def add_months(
    sourcedate,
    months: int,
    fix_march_to_max: bool = True,
    days_360: bool = False,
):
    """
    Add specified month(s) to provided source date
    :param sourcedate: The initial date or datetime
    :param months: The number of months
    :param fix_march_to_max: From feb to march leaves the max(31)
    :param days_360: Calculates date days in 360 format
    :return: An integer representing day difference
    :raise ValueError: if provided dates are not valid
    """
    if type(sourcedate) is str:
        try:
            sourcedate = str_to_date(sourcedate)
        except ValueError:
            sourcedate = str_to_datetime(sourcedate)

    if type(sourcedate) is not date and type(sourcedate) is not datetime:
        raise ValueError("Provided sourcedate is not a valid date or datetime")

    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, monthrange(year, month)[1])

    if fix_march_to_max and (month == 3):
        day = max(sourcedate.day, monthrange(year, month)[1])

    if days_360:
        day = 28 if (month == 2) else 30

    if type(sourcedate) is date:
        new_date = date(year, month, day)
    else:
        new_date = datetime(
            year, month, day, sourcedate.hour,
            sourcedate.minute, sourcedate.second
        )

    return new_date


def days360(
    start_date, end_date, method_eu: bool = False
) -> int:
    """
    Calculates day difference between two dates using 360 days format
    :param start_date:
    :param end_date:
    :param method_eu:
    :return: An integer representing day difference
    :raise ValueError: if provided dates are not valid
    """

    if type(start_date) is str:
        start_date = str_to_date(start_date)

    if type(end_date) is str:
        end_date = str_to_date(end_date)

    start_day = start_date.day
    start_month = start_date.month
    start_year = start_date.year
    end_day = end_date.day
    end_month = end_date.month
    end_year = end_date.year

    if start_day == 31 or (
        method_eu is False
        and start_month == 2
        and (start_day == 29 or (
            start_day == 28 and isleap(start_year) is False)
        )
    ):
        start_day = 30

    if end_day == 31:
        if method_eu is False and start_day != 30:
            end_day = 1

            if end_month == 12:
                end_year += 1
                end_month = 1
            else:
                end_month += 1
        else:
            end_day = 30

    return (
        end_day
        + end_month * 30
        + end_year * 360
        - start_day
        - start_month * 30
        - start_year * 360
    )


def str_to_date(date_as_str: str, date_format: str = "%Y-%m-%d") -> date:
    """
    Cast string to date
    :param date_as_str: Date as string
    :param date_format: Date format
    :return: datetime object
    :raise ValueError if provided date is not a valid string
    """
    if type(date_as_str) is not str:
        raise ValueError("Provided date is not a valid string")

    return datetime.strptime(date_as_str, date_format).date()


def str_to_datetime(
    date_as_str: str, date_format: str = "%Y-%m-%d %H:%M:%S"
) -> datetime:
    """
    Cast string to date
    :param date_as_str: Datetime as string
    :param date_format: Datetime format
    :return: datetime object
    :raise ValueError if provided date is not a valid string
    """
    if type(date_as_str) is not str:
        raise ValueError("Provided datetime is not a valid string")

    return datetime.strptime(date_as_str, date_format)


def reduce_and_add(list_to_reduce: list):
    return reduce(operator_add, list_to_reduce)


def update_and_add_dict(
    initial_dict: dict,
    exclude_dict: list = [],
    if_key_exists: bool = False,
    **values
) -> dict:
    """
    Verifies if key exists in original_dict and adds value to it. In case key
    does not exist in original_dict, key is set as new
    :param initial_dict:
    :param values: Keys to add
    :param exclude_dict: Keys to exclude
    :param if_key_exists: Adds value to dict only if key exists when True
    :return: Original dict with added values
    """
    for key, value in values.items():
        #
        if (initial_dict.get(key, None) is None) and (not if_key_exists):
            initial_dict[key] = value
        elif key not in exclude_dict:
            initial_dict[key] += value

    return initial_dict


def month_diff(start_date, end_date) -> int:
    """
    Calculates the month difference between two dates.
    !WARNING: Note days are not used in this function
    :param start_date: A Y-m-d formatted date
    :param end_date: A Y-m-d formatted date
    :return: The number of months between the dates
    :raise ValueError: If start date is greater than end date.
    """

    if type(start_date) is str:
        start_date = str_to_date(start_date)

    if type(end_date) is str:
        end_date = str_to_date(end_date)

    start_month: int = start_date.month
    start_year: int = start_date.year
    end_month: int = end_date.month
    end_year: int = end_date.year

    if start_year == end_year:
        diff: int = end_month - start_month
    elif start_year < end_year:
        diff: int = (12 - start_month) + end_month
    else:
        raise ValueError("Start date cannot be greater than end date")

    return diff


def day_diff(start_date, end_date) -> int:
    """
    Calculates the month difference between two dates.
    :param start_date: A Y-m-d formatted date
    :param end_date: A Y-m-d formatted date
    :return: The number of months between the dates
    :raise ValueError: If start date is greater than end date.
    """

    if type(start_date) is str:
        start_date = str_to_date(start_date)

    if type(end_date) is str:
        end_date = str_to_date(end_date)

    return (start_date - end_date).days


def extract_from_date(date_, key: str) -> int:
    """
    Extract the day, month or year from a date
    :param date_: A Y-m-d formatted date
    :param key: Could be 'day', 'month' or 'year'
    :return: An int representing the selected key
    :raise ValueError: If an invalid key is provided
    """

    if type(date_) is str:
        date_ = str_to_date(date_)

    key_list = {"day": date_.day, "month": date_.month, "year": date_.year}

    if key not in key_list:
        raise ValueError(
            "Invalid key provided. Existing values are: " "day, month, year"
        )

    return key_list[key]


def cast_dict_decimal_to_float(data: dict) -> dict:
    """Casts decimal values of dictionary to float

    Args:
        data: The dictionary whose values will be cast

    Returns:
        The dictionary with no decimal values
    """
    # For every value in data
    for k, value in data.items():

        # Cast it to float when its original type is decimal
        if type(value) is Decimal:
            data[k] = float(value)

    return data


def calculate_age(birthdate) -> int:
    """Calculates age based on birthdate for a customer"""
    # Casting if a str is provided
    if type(birthdate) is str:
        birthdate = str_to_date(birthdate)

    # Getting today date
    today = date.today()
    # Calculating
    age = (
        today.year
        - birthdate.year
        - ((today.month, today.day) < (birthdate.month, birthdate.day))
    )
    return age


def cast_dict_to_int(data: dict) -> dict:
    """Casts dict values to int

    Args:
        data: The dictionary whose values will be cast

    Returns:
        The dictionary with no decimal values
    """
    # For every value in data
    for k, value in data.items():

        # Cast it to int when possible
        try:
            data[k] = int(value)
        except (TypeError, ValueError):
            pass

    return data


def convert_rate_EA_to_EM(annual_rate: float, factor: int = 1) -> float:
    """
    Converts from Effective Annual to Effective Monthly.
    Args:
        annual_rate (float): The annual rate.
        factor (int, optional): The monthy factor. Defaults to 1.
    Returns:
        float: The monthly rate by the factor.
    """
    return pow((1 + (annual_rate / 100)), (factor / 12)) - 1
