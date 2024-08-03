from machine import RTC


def datetime_string():
    """
    Returns datetime string from the pico's RTC

    Returns:
      str: datetime string of current time (format YYYY-mm-dd HH:MM:SS)
    """
    now = RTC().datetime()
    return "{0:04d}-{1:02d}-{2:02d} {4:02d}:{5:02d}:{6:02d}".format(*now)
