from os import stat, remove, rename


class Logging:
    """Handles logging info/warnings/errors/etc to log file"""

    def __init__(self):
        # values for keeping log file from taking up too much space, in bytes
        self.__truncate_at = 11 * 1024
        self.__tuncate_to = 8 * 1024

    def log_size(self, file):
        """
        Get size of the log file

        Args:
          file (obj): File object of the log file

        Returns:
          int: Size of log file
          None: On error
        """
        try:
            return stat(file)[6]
        except OSError:
            return None

    def truncate(self, file, target_size):
        """
        Truncate log file to desired size

        Args:
          file (obj): Log file object
          target_size (int): Desired size of log file in bytes
        """
        cur_size = self.log_size(file)

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
