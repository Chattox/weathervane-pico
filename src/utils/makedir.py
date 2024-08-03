from os import mkdir
from errno import EEXIST


def makedir(dir):
    """
    Create new directory folder with checks for if folder already exists

    Args:
      dir (str): name of folder to create
    """
    try:
        mkdir(dir)
    except OSError as e:
        if e.errno != EEXIST:
            raise
        pass  # If dir already exists, this is fine
