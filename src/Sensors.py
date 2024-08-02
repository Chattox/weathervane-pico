from time import sleep_ms
from ucollections import OrderedDict
from breakout_bme280 import BreakoutBME280
from breakout_ltr559 import BreakoutLTR559


class Sensors:
    """
    Handles the config and reading of the on-board and external sensors

    Args:
      i2c (PimoroniI2C): I2C controller for passing to sensor controllers
    """

    def __init__(self, i2c):
        self.__bme280 = BreakoutBME280(i2c, 0x77)
        self.__ltr559 = BreakoutLTR559(i2c)

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

        readings_data = OrderedDict(
            [
                ("temperature", round(bme280_data[0], 2)),
                ("humidity", round(bme280_data[2], 2)),
                ("pressure", round(bme280_data[1] / 100.0, 2)),
                (
                    "luminance",
                    round(ltr_data[BreakoutLTR559.LUX] if ltr_data else 0, 2),
                ),
            ]
        )

        print(readings_data)
