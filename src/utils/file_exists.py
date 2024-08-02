from os import stat


def file_exists(filename):
    """
    Check if file exists

    Args:
      filename (str): name of target file

    Returns:
      bool: True if exists, false if not
    """
    try:
        return (stat(filename)[0] & 0x4000) == 0
    except OSError:
        return False
