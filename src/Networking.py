from time import sleep_ms, ticks_ms
from rp2 import country
from network import STA_IF, WLAN, hostname
from math import ceil
from ubinascii import hexlify
from utils.constants import (
    CYW43_LINK_DOWN,
    CYW43_LINK_JOIN,
    CYW43_LINK_UP,
    CYW43_STATUS_NAMES,
)
from utils.uid import uid
from utils.config import WIFI_COUNTRY, WIFI_HOSTNAME, WIFI_PASSWORD, WIFI_SSID


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
