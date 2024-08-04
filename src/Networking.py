from os import ilistdir, listdir, remove
from time import gmtime, sleep_ms, ticks_ms
from rp2 import country
from network import STA_IF, WLAN, hostname
from math import ceil
from ubinascii import hexlify
from ntptime import time
from machine import RTC
from urequests import post
from ujson import load
from utils.constants import (
    CYW43_LINK_DOWN,
    CYW43_LINK_JOIN,
    CYW43_LINK_UP,
    CYW43_STATUS_NAMES,
)
from utils.config import (
    UPLOAD_DESTINATION,
    WIFI_COUNTRY,
    WIFI_HOSTNAME,
    WIFI_PASSWORD,
    WIFI_SSID,
)
from utils.cached_reading_count import cached_reading_count
from utils.file_exists import file_exists
from utils.uid import uid


class Networking:
    """
    Handles all networking/wifi functionality (including syncing RTC to NTP server)

    Args:
      logger (Logging): Logging controller for logging info to file
      is_usb_powered (int): Whether board is USB powered or not. Value from VBUS pin reading
    """

    def __init__(self, logger, is_usb_powered):
        self.__logger = logger
        self.__is_usb_powered = is_usb_powered
        # Don't initialise wlan until it's necessary
        self.__wlan = None

    def connect(self):
        """
        Connect to wifi network

        Raises:
          Exception: On wifi network failure
        """
        start_ms = ticks_ms()

        # Set country for wifi connection
        country(WIFI_COUNTRY)

        # Set hostname
        host_name = WIFI_HOSTNAME
        if host_name is None:
            host_name = f"Weathervane-{uid()[-4:]}"
        hostname(host_name)

        self.__wlan = WLAN(STA_IF)
        self.__wlan.active(True)

        # If USB powered, disable power saving mode
        if self.__is_usb_powered:
            self.__wlan.config(pm=0xA11140)

        self.__logger.info("Preparing to connect to wifi...")

        # If already connected, disconnect first
        status = self.__get_status()
        if status >= CYW43_LINK_JOIN and status < CYW43_LINK_UP:
            self.disconnect()

        self.__logger.info("- Ready to connect!")

        # Start connection process
        self.__logger.info(f"Connecting to wifi network: {WIFI_SSID}...")
        mac = hexlify(self.__wlan.config("mac"), ":").decode()
        self.__logger.info(f"- Device MAC addr: {mac}")

        self.__wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        try:
            self.__await_status(CYW43_LINK_UP)
        except Exception as x:
            raise Exception(f"Failed to connect to network {WIFI_SSID}: {x}")
        self.__logger.info("- Connected successfully!")

    def __get_status(self):
        """
        Get status of wifi connection

        Returns:
          Wifi connection status as defined in utils.constants
        """
        if self.__wlan is None:
            self.__logger.error("WLAN not initialised")
            return CYW43_LINK_DOWN

        status = self.__wlan.status()
        self.__logger.info(
            f"- active: {1 if self.__wlan.active() else 0}, status: {status} ({CYW43_STATUS_NAMES[status]})"
        )
        return status

    def __await_status(self, expected_status, timeout=10000, sleep_dur=500):
        """
        Await a specific wifi connection status with timeout

        Args:
          expected_status (int): Wifi status to wait for (defined in utils.constants)
          timeout (int): Amount of time to wait for status before declaring failure in ms
          sleep_dur (int): Amount of time to sleep between each status check in ms

        Returns:
          bool: True if expected status returned, False if timeout hit without expected status

        Raises:
          Exception: If error status received
        """
        for i in range(ceil(timeout / sleep_dur)):
            sleep_ms(sleep_dur)
            status = self.__get_status()
            if status == expected_status:
                return True
            elif status < 0:
                raise Exception(CYW43_STATUS_NAMES[status])
        return False

    def disconnect(self):
        """
        Disconnect from wifi network

        Raises:
          Exception: On disconnection failure
        """
        self.__logger.info(f"Disconnecting from wifi network: {WIFI_SSID}...")

        if self.__wlan is None:
            self.__logger.warn("- WLAN not initialised, so assuming disconnected")
            return

        self.__wlan.disconnect()
        try:
            self.__await_status(CYW43_LINK_DOWN)
        except Exception as x:
            raise Exception(f"Failed to disconnect: {x}")
        self.__logger.info("- Successfully disconnected")

    def sync_rtc_from_ntp(self, i2c, rtc):
        """
        Connect to wifi and sync RTC chip to time from an NTP server

        Args:
            i2c (PimoroniI2C): I2C to enable setting RTC chip time
            rtc (PCF85063A): Controller for RTC chip

        Returns:
            bool: True if RTC set correctly, False if not

        """
        self.__logger.info("Syncing RTC to NTP server")
        self.connect()

        # Fetch current timestamp from NTP server and convert to usable tuple
        timestamp = time()
        if not timestamp:
            self.__logger.error("- Failed to fetch time from NTP server")
            return
        timestamp = gmtime(timestamp)
        self.disconnect()

        # Set RTC chip to new time
        i2c.writeto_mem(0x51, 0x00, b"\x10")  # Reset RTC to change time
        rtc.datetime(timestamp)  # Set time on RTC chip
        i2c.writeto_mem(0x51, 0x00, b"\x00")  # Ensure RTC chip is running
        rtc.enable_timer_interrupt(False)

        # Check the new RTC time to make sure it updated successfully
        dt = rtc.datetime()
        if dt != timestamp[0:7]:
            # Remove last_rtc_sync.txt to trigger reattempt next time
            if file_exists("last_rtc_sync.txt"):
                remove("last_rtc_sync.txt")
            return False

        # Sync pico RTC too
        RTC().datetime((dt[0], dt[1], dt[2], dt[6], dt[3], dt[4], dt[5], 0))

        self.__logger.info("- RTC synced successfully")

        # Write latest sync time to file
        with open("last_rtc_sync.txt", "w") as syncfile:
            syncfile.write(
                "{0:04d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}Z".format(*timestamp)
            )

        return True

    def upload_readings(self):
        """
        Upload cached readings to http endpoint
        """
        self.__logger.info("Preparing to upload readings...")
        self.connect()

        self.__logger.info(
            f"Uploading {cached_reading_count()} cached reading(s) to {UPLOAD_DESTINATION}..."
        )

        # Upload each cached reading in turn
        for reading_file in ilistdir("uploads"):
            try:
                with open(f"uploads/{reading_file[0]}", "r") as upload_file:
                    try:
                        res = post(
                            UPLOAD_DESTINATION, auth=None, json=(load(upload_file))
                        )
                        res.close()

                        # If upload successful, delete cached upload
                        if res.status_code in [200, 201, 202]:
                            remove(f"uploads/{reading_file[0]}")
                            self.__logger.info(f"- Uploaded {reading_file[0]}")
                        else:
                            self.__logger.error(
                                f"- Upload of {reading_file[0]} failed. Status: {res.status_code}, Reason: {res.reason}"
                            )

                    except Exception as x:
                        self.__logger.exception(
                            f"- An exception occurred when uploading: {x}"
                        )

            except OSError:
                self.__logger.error(f"- Failed to open '{reading_file[0]}'")

        # Finally, disconnect from wifi
        self.disconnect()
