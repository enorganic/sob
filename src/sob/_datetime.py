from __future__ import annotations

from datetime import date, datetime

from iso8601.iso8601 import parse_date


def date2str(date_value: date) -> str:
    """
    Return an ISO-8601 formatted representation of an instance of
    `datetime.date`.

    >>> date2str(date(2023, 10, 1))
    '2023-10-01'
    """
    if (not isinstance(date_value, date)) or isinstance(date_value, datetime):
        raise TypeError(date_value)
    return date_value.isoformat()


def datetime2str(datetime_value: datetime) -> str:
    """
    Return an ISO-8601 formatted representation of an instance of
    `datetime.datetime`.

    Examples:

    >>> datetime2str(datetime(2023, 10, 1, 12, 0, 0))
    '2023-10-01T12:00:00Z'
    >>> from datetime import timezone, timedelta
    >>> datetime2str(datetime(2023, 10, 1, 12, 0, 0, tzinfo=timezone.utc))
    '2023-10-01T12:00:00+00:00'
    >>> from datetime import timezone
    >>> pacific_time: timezone = timezone(timedelta(hours=-8))
    >>> datetime2str(datetime(2023, 10, 1, 12, 0, 0, tzinfo=pacific_time))
    '2023-10-01T12:00:00-08:00'
    """
    if not isinstance(datetime_value, datetime):
        raise TypeError(datetime_value)
    string_value: str = datetime_value.isoformat()
    if (datetime_value.tzinfo is None) and not string_value.endswith("Z"):
        string_value = f"{string_value}Z"
    return string_value


def str2datetime(str_value: str) -> datetime:
    """
    Return an instance of `datetime.datetime` from an ISO-8601 formatted
    string representation.

    Examples:

    >>> str2datetime("2023-10-01T12:00:00Z")
    datetime.datetime(2023, 10, 1, 12, 0, tzinfo=datetime.timezone.utc)
    >>> str2datetime("2023-10-01T12:00:00")
    datetime.datetime(2023, 10, 1, 12, 0)
    """
    if not isinstance(str_value, str):
        raise TypeError(str_value)
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
            and len(str_value.split("-")) == 3  # noqa: PLR2004
            and (datetime_value.tzinfo is not None)
        ):
            datetime_value = datetime_value.replace(tzinfo=None)
    return datetime_value


def str2date(str_value: str) -> date:
    """
    Return an instance of `datetime.date` from an ISO-8601 formatted
    string representation.

    Examples:

    >>> str2date("2023-10-01")
    datetime.date(2023, 10, 1)
    """
    if not isinstance(str_value, str):
        raise TypeError(str_value)
    return date.fromisoformat(str_value)
