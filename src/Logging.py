from os import stat, remove, rename
from utils.datetime_string import datetime_string


class Logging:
    """Handles logging info/warnings/errors/etc to log file"""

    def __init__(self):
        # values for keeping log file from taking up too much space, in bytes
        self.__truncate_at = 11 * 1024
        self.__truncate_to = 8 * 1024
        # name of log file
        self.__log_file = "log.txt"

    def __log_size(self, file):
        """
        Get size of the log file

        Args:
          file (str): Filename of log file

        Returns:
          int: Size of log file
          None: On error
        """
        try:
            return stat(file)[6]
        except OSError:
            return None

    def __truncate(self, file, target_size):
        """
        Truncate log file to desired size

        Args:
          file (str): Filename of log file
          target_size (int): Desired size of log file in bytes
        """
        cur_size = self.__log_size(file)

        # figure out how many bytes to remove from log file
        discard_size = cur_size - target_size
        if discard_size <= 0:
            return

        with open(file, "rb") as in_file:
            with open(file + ".tmp", "wb") as out_file:
                # skip through input file until discard enough
                while discard_size > 0:
                    chunk = in_file.read(1024)
                    discard_size -= len(chunk)

                # find a line break nearby
                break_pos = max(
                    chunk.find(b"\n", -discard_size), chunk.rfind(b"\n", -discard_size)
                )
                if break_pos != -1:
                    out_file.write(chunk[break_pos + 1 :])

                # copy rest of file
                while True:
                    chunk = in_file.read(1024)
                    if not chunk:
                        break
                    out_file.write(chunk)

        # delete old file and replace with new
        remove(file)
        rename(file + ".tmp", file)

    def log(self, level, text):
        """
        Save logging data to log file

        Args:
          level (str): logging level such as debug, error, etc
          text (str): content of log
        """
        datetime = datetime_string()
        # append datetime string to log entry
        log_entry = "{0} [{1}] {2}".format(datetime, level, text)
        print(log_entry)
        # write to file with newline
        with open(self.__log_file, "a") as logfile:
            logfile.write(log_entry + "\n")

        # if log file is getting too big, truncate
        if self.__truncate_at and self.__log_size(self.__log_file):
            self.__truncate(self.__log_file, self.__truncate_to)
