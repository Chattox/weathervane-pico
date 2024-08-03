from machine import RTC


def datetime_string(for_filename=False):
    """
    Returns datetime string from the pico's RTC

    Args:
      for_filename (bool): Whether this is for a filename or not. Just
      decides whether time is separated with : or _

    Returns:
      str: datetime string of current time (format YYYY-mm-dd HH:MM:SS)
    """
    now = RTC().datetime()
    if for_filename:
        return "{0:04d}-{1:02d}-{2:02d}_{4:02d}-{5:02d}-{6:02d}".format(*now)
    else:
        return "{0:04d}-{1:02d}-{2:02d} {4:02d}:{5:02d}:{6:02d}".format(*now)
