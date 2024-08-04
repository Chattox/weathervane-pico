from time import sleep_ms
from Weathervane import Weathervane
from utils.constants import WARN_LED_OFF

# Sleep for 0.5 seconds to fix https://github.com/micropython/micropython/issues/9605
sleep_ms(500)

station = Weathervane()

try:
    # Turn off warn LED in case it's currently going
    station.set_warn_led(WARN_LED_OFF)

    station.startup()

    if not station.is_clock_set():
        station.logger.info("RTC not set, syncing from NTP server")
        station.networking.sync_rtc_from_ntp(station.i2c, station.rtc)

    station.take_reading()

    station.networking.upload_readings()

except Exception as x:
    print(x)
