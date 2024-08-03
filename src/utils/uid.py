from machine import unique_id


def uid():
    """
    Creates unique ID for the device to be used as the hostname

    Returns:
      str: Unique ID for the device
    """
    return "{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}".format(*unique_id())
