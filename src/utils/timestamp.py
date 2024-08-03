from time import mktime
from utils.datetime_string import datetime_string


def timestamp(dt=datetime_string()):
    """
    Creates a unix style timestamp from a given datetime string

    Note:
      Returns a timestamp based on *local* machine time, not necessarily UTC
      but the RTC syncs to UTC anyway.
      If no datetime string is supplied, defaults to current local time

    Args:
      dt (str): Datetime string e.g. 2024-08-03 12:47:43

    Returns:
      int: unix style timestamp of dt
    """
    year = int(dt[0:4])
    month = int(dt[5:7])
    day = int(dt[8:10])
    hour = int(dt[11:13])
    minute = int(dt[14:16])
    second = int(dt[17:19])

    # Pylance ignore following line as mktime's intellisense is messed up and thinks it
    # shouldn't take an argument when actually it should
    return mktime((year, month, day, hour, minute, second, 0, 0))  # type: ignore
