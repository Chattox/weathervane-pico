from time import sleep_ms
from Weathervane import Weathervane
from utils.constants import WARN_LED_OFF
from utils.config import UPLOAD_FREQUENCY
from utils.cached_reading_count import cached_reading_count

# Sleep for 0.5 seconds to fix https://github.com/micropython/micropython/issues/9605
sleep_ms(500)

station = Weathervane()

try:
    # Turn off warn LED in case it's currently going
    station.set_warn_led(WARN_LED_OFF)

    # Initial startup process
    station.startup()

    # Make sure RTC chip is set correctly
    if not station.is_clock_set():
        station.logger.info("RTC not set, syncing from NTP server")
        clock_set = station.networking.sync_rtc_from_ntp(station.i2c, station.rtc)
        if not clock_set:
            station.error("- Failed to synchronise RTC")

    # Log space remaining in pico storage
    station.space_remaining()

    # Take readings from sensors and cache them
    station.take_reading()

    cache_count = cached_reading_count()
    if cache_count >= UPLOAD_FREQUENCY:
        station.logger.info(f"{cache_count} cached readings to upload")
        station.networking.upload_readings()
    else:
        station.logger.info(
            f"Not enough cached readings to upload ({cache_count} readings). Waiting until there are {UPLOAD_FREQUENCY} readings"
        )

    station.sleep()

except Exception as x:
    station.exception(x)
