from machine import Pin
from time import sleep_ms, ticks_ms, ticks_diff
from math import pi
from ucollections import OrderedDict
from breakout_bme280 import BreakoutBME280
from breakout_ltr559 import BreakoutLTR559
from utils.constants import WIND_SPEED_PIN, WIND_RADIUS_CM, WIND_FACTOR


class Sensors:
    """
    Handles the config and reading of the on-board and external sensors

    Args:
      i2c (PimoroniI2C): I2C controller for passing to sensor controllers
    """

    def __init__(self, i2c):
        self.__bme280 = BreakoutBME280(i2c, 0x77)
        self.__ltr559 = BreakoutLTR559(i2c)
        self.__wind_speed_pin = Pin(WIND_SPEED_PIN, Pin.IN, Pin.PULL_UP)

    def __get_wind_speed(self, sample_time_ms=1000):
        """
        Calculate wind speed from anemometer.

        Track the number of times the value from the anemometer changes within a
        certain time period (`sample_time_ms`) and the amount of time between
        those changes.

        Args:
          sample_time_ms (int): ms to monitor anemometer output for

        Returns:
          int: wind speed in m/s
        """
        # Get initial sensor value
        state_val = self.__wind_speed_pin.value()

        # Array to log times sensor value changes
        ticks = []

        start = ticks_ms()

        # Get values from the anemometer for duration of sample_time_ms
        while ticks_diff(ticks_ms(), start) <= sample_time_ms:
            cur_val = self.__wind_speed_pin.value()
            if cur_val != state_val:
                # If value has changed, record time of change and update state_val
                ticks.append(ticks_ms())
                state_val = cur_val

        # If anemometer isn't connected there won't be any extra ticks, so skip everything else
        if len(ticks) < 2:
            return 0

        # Calculate the average tick time between changes (in ms)
        average_tick_ms = (ticks_diff(ticks[-1], ticks[0])) / (len(ticks) - 1)

        # Just in case the average is 0, skip the rest to avoid division errors
        if average_tick_ms == 0:
            return 0

        # Work out the rotation speed in Hz (2 ticks per rotation)
        rotation_hz = (1000 / average_tick_ms) / 2

        # Calculate the wind speed in metres per second
        circumference = WIND_RADIUS_CM * 2.0 * pi
        wind_speed = rotation_hz * circumference * WIND_FACTOR

        return wind_speed

    def get_sensor_readings(self):
        """
        Take readings from all sensors and return a dict containing them

        Note:
          May eventually want to add temperature compensation for running
          on USB power heating things up

        Returns:
          dict (OrderedDict): sensor readings
        """
        # The BME280 returns the register contents first and then takes a new reading
        # so run a dummy read first to discard register contents and get current data
        self.__bme280.read()
        sleep_ms(100)
        bme280_data = self.__bme280.read()

        ltr_data = self.__ltr559.get_reading()

        wind_speed = self.__get_wind_speed()

        readings_data = OrderedDict(
            [
                ("temperature", round(bme280_data[0], 2)),
                ("humidity", round(bme280_data[2], 2)),
                ("pressure", round(bme280_data[1] / 100.0, 2)),
                (
                    "luminance",
                    round(ltr_data[BreakoutLTR559.LUX] if ltr_data else 0, 2),
                ),
                ("wind_speed", wind_speed),
            ]
        )

        print(readings_data)
