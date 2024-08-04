from os import listdir


def cached_reading_count():
    """
    Get the number of cached readings waiting for upload

    Returns:
        int: Number of cached readings waiting for upload
    """
    try:
        return len(listdir("uploads"))
    except OSError:
        return 0
