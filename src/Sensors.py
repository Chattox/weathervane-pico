from os import remove
from machine import Pin
from time import sleep_ms, ticks_ms, ticks_diff
from math import pi
from pimoroni import Analog
from ucollections import OrderedDict
from breakout_bme280 import BreakoutBME280
from breakout_ltr559 import BreakoutLTR559
from utils.constants import (
    RAIN_MM_PER_TICK,
    RAIN_PIN,
    WIND_DIR_PIN,
    WIND_SPEED_PIN,
    WIND_RADIUS_CM,
    WIND_FACTOR,
)
from utils.datetime_string import datetime_string
from utils.file_exists import file_exists
from utils.timestamp import timestamp


class Sensors:
    """
    Handles the config and reading of the on-board and external sensors

    Args:
        logger (Logging): Logging controller for logging info to file
        i2c (PimoroniI2C): I2C controller for passing to sensor controllers,
        act_led (ActivityLED): Controller for controlling activity LED on enviro board
    """

    def __init__(self, logger, i2c, act_led):
        self.__logger = logger
        self.__bme280 = BreakoutBME280(i2c, 0x77)
        self.__ltr559 = BreakoutLTR559(i2c)
        self.__wind_speed_pin = Pin(WIND_SPEED_PIN, Pin.IN, Pin.PULL_UP)
        self.__wind_dir_pin = Analog(WIND_DIR_PIN)
        self.__rain_pin = Pin(RAIN_PIN, Pin.IN, Pin.PULL_DOWN)
        self.__prev_rain_trigger = False
        self.__activity_led = act_led

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

    def __get_wind_dir(self):
        """
        Gets wind direction heading.

        Converts the voltage reading given by the wind direction pin into degrees.
        Finds the closest value from an array of 45 degree heading increments and returns it

        Note:
          The wind direction is read using Pimoroni's own Analog class, which does some
          skullduggery behind the scenes to correct the returned values a bit

        Returns:
          int: Wind direction heading in degrees
        """
        ADC_TO_DEGREES = (0.9, 2.0, 3.0, 2.8, 2.5, 1.5, 0.3, 0.6)

        closest_index = -1
        last_index = None

        # Make sure there are 2 readings in a row that much as if readings are taken
        # during transition between two values it can bug out
        while True:
            value = self.__wind_dir_pin.read_voltage()

            closest_index = -1
            closest_value = float("inf")

            for i in range(8):
                distance = abs(ADC_TO_DEGREES[i] - value)
                if distance < closest_value:
                    closest_value = distance
                    closest_index = i

            # If 2 matching values in a row, exit the loop
            if last_index == closest_index:
                break

            last_index = closest_index

        return closest_index * 45

    def check_rain_sensor(self, wakeup=False):
        """
        Check rain sensor and if rain detected, log rain event.

        Used either as part of the monitoring state the board goes into when
        in sleep mode but on USB power or when the board is battery powered and
        woken up from sleep mode by the rain sensor trigger

        Args:
          wakeup (bool): If true, skip getting pin value and go straight to logging rain event
        """
        if not wakeup:
            rain_val = self.__rain_pin.value()

        # Make sure the rain sensor has triggered and hasn't already been
        # triggered this wake to prevent duplicate entries
        if wakeup or (rain_val and not self.__prev_rain_trigger):
            self.__activity_led.set_brightness(100)
            sleep_ms(50)
            self.__activity_led.set_brightness(0)

            # Read in current rain entries
            rain_entries = []
            if file_exists("rain.txt"):
                with open("rain.txt", "r") as rainfile:
                    rain_entries = rainfile.read().split("\n")

            # Add the new entry
            dt_str = datetime_string()
            self.__logger.info(f"Adding new rain trigger at {dt_str}")
            rain_entries.append(dt_str)

            # Limit number of entries to 190; each entry is ~21 bytes including newline
            # so this keeps total filesize to just under one filesystem block (4096 bytes)
            rain_entries = rain_entries[-190:]

            # Write the new rain log
            with open("rain.txt", "w") as rainfile:
                rainfile.write("\n".join(rain_entries))

        self.__prev_rain_trigger = True if wakeup else rain_val

    def __get_rainfall(self, seconds_since_last):
        """
        Calculate the amount of rainfall since the last time function was called.

        Also calculate the rainfall per second because why not

        Args:
            seconds_since_last (int): Seconds since the last reading was taken

        Returns:
            float, float: Amount of rainfall in mm, Rate of rainfall in mm/s
        """
        rain_amount = 0
        per_second = 0
        cur_timestamp = timestamp(datetime_string())

        if file_exists("rain.txt"):
            with open("rain.txt", "r") as rainfile:
                rain_entries = rainfile.read().split("\n")

            # Count how many rain entries there have been since the last reading
            for entry in rain_entries:
                if entry:
                    ts = timestamp(entry)
                    if cur_timestamp - ts < seconds_since_last:
                        rain_amount += RAIN_MM_PER_TICK

            # Once done, remove rain.txt to clear old readings
            remove("rain.txt")

        # If it's rained at all, calculate rain per second
        if rain_amount > 0 and seconds_since_last > 0:
            per_second = rain_amount / seconds_since_last

        return rain_amount, per_second

    def get_sensor_readings(self):
        """
        Take readings from all sensors and return a dict containing them

        Note:
          May eventually want to add temperature compensation for running
          on USB power heating things up

        Args:
            seconds_since_last (int): Seconds elapsed since last reading was taken

        Returns:
          dict (OrderedDict): sensor readings
        """
        self.__logger.info("Taking new reading...")

        seconds_since_last = 0

        now_str = datetime_string()
        if file_exists("last_reading_time.txt"):
            now_ts = timestamp(now_str)

            with open("last_reading_time.txt", "r") as timefile:
                last_time = timefile.readline()
                last_ts = timestamp(last_time)

            seconds_since_last = now_ts - last_ts
            self.__logger.info(
                f"- Seconds since last reading: {seconds_since_last}")

        # The BME280 returns the register contents first and then takes a new reading
        # so run a dummy read first to discard register contents and get current data
        self.__bme280.read()
        sleep_ms(100)
        bme280_data = self.__bme280.read()
        ltr_data = self.__ltr559.get_reading()
        wind_speed = self.__get_wind_speed()
        wind_direction = self.__get_wind_dir()
        rain, rain_per_second = self.__get_rainfall(seconds_since_last)

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
                ("rain", rain),
                ("rain_per_second", rain_per_second),
                ("wind_direction", wind_direction),
            ]
        )

        # Log time of reading for next time
        with open("last_reading_time.txt", "w") as timefile:
            timefile.write(now_str)

        return readings_data
