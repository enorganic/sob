from datetime import date, datetime

from iso8601.iso8601 import parse_date


def date2str(date_value: date) -> str:
    """
    Return an ISO-8601 formatted representation of an instance of
    `datetime.date`.
    """
    assert isinstance(date_value, date) and not isinstance(
        date_value, datetime
    )
    return date_value.isoformat()


def datetime2str(datetime_value: datetime) -> str:
    """
    Return an ISO-8601 formatted representation of an instance of
    `datetime.datetime`.
    """
    assert isinstance(datetime_value, datetime)
    string_value: str = datetime_value.isoformat()
    if (datetime_value.tzinfo is None) and not string_value.endswith("Z"):
        string_value = f"{string_value}Z"
    return string_value


def str2datetime(str_value: str) -> datetime:
    """
    Return an instance of `datetime.datetime` from an ISO-8601 formatted
    string representation.
    """
    assert isinstance(str_value, str)
    datetime_value: datetime
    try:
        datetime_value = datetime.fromisoformat(str_value)
    except ValueError:
        datetime_value = parse_date(str_value)
        # `iso8601` incorrectly sets the UTC offset to `0` instead of `None`
        # when no time zone is provided
        if (
            str_value.endswith("Z")
            and "+" not in str_value
            and len(str_value.split("-")) == 3
            and (datetime_value.tzinfo is not None)
        ):
            datetime_value = datetime_value.replace(tzinfo=None)
    return datetime_value


def str2date(str_value: str) -> date:
    """
    Return an instance of `datetime.date` from an ISO-8601 formatted
    string representation.
    """
    assert isinstance(str_value, str)
    return date.fromisoformat(str_value)
