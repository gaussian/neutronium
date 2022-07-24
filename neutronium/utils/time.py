import datetime

from backports.zoneinfo import ZoneInfo


def get_time_ago(num_days, time_ago_from=None, set_time_to_midnight=False):

    # Default is time ago from today
    if time_ago_from is None:
        time_ago_from = datetime.datetime.now(tz=ZoneInfo("UTC"))

    # Set the time portion to be 0 for midnight
    if set_time_to_midnight:
        time_ago_from = time_ago_from.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    # Return now minus the number of days
    return time_ago_from - datetime.timedelta(days=num_days)


def get_time_diff_days(time_til, time_ago_from=None):

    # Default is time ago from today
    if time_ago_from is None:
        time_ago_from = datetime.datetime.now(tz=ZoneInfo("UTC"))

    diff = time_til - time_ago_from

    return diff.days


def get_year_start(year):
    return datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0, tzinfo=ZoneInfo("UTC"))


def get_year_end(year):
    return datetime.datetime(year=year, month=12, day=31, hour=23, minute=59, second=59, tzinfo=ZoneInfo("UTC"))


def get_day_start(date):
    return datetime.datetime.combine(date, datetime.datetime.min.time())


# def separate_years_from_texts(texts):
#     return separate_ints_from_texts(texts, acceptable_range=(100, 2100))


def localize_to_utc(date):

    # If date exists
    if date:

        # If date is timezone-naive
        if date.tzinfo is None or date.tzinfo.utcoffset(date) is None:
            return date.replace(tzinfo=ZoneInfo("UTC"))

        # If has timezone, set timezone as UTC
        return date.astimezone(ZoneInfo("UTC"))

    # None otherwise
    return None


def validate_date(date):

    if not date:
        return False

    now = datetime.datetime.now(tz=ZoneInfo("UTC"))
    if date > now + datetime.timedelta(days=15) or date < datetime.datetime(1971, 1, 1, tzinfo=ZoneInfo("UTC")):
        return False

    return True


SERIALIZATION_DATE_FORMAT = "%m-%d-%Y, %H:%M:%S %z"


def serialize_date(date: datetime.datetime) -> str:
    return date.strftime(SERIALIZATION_DATE_FORMAT)


def deserialize_date(date: str) -> datetime.datetime:
    return datetime.datetime.strptime(date, SERIALIZATION_DATE_FORMAT)
