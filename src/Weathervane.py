from machine import RTC
from pimoroni_i2c import PimoroniI2C
from pcf85063a import PCF85063A
from constants import I2C_SDA_PIN, I2C_SCL_PIN
from ActivityLED import ActivityLED


class Weathervane:
    """Handles overall functionality of the enviro board"""

    def __init__(self):
        self.i2c = PimoroniI2C(I2C_SDA_PIN, I2C_SCL_PIN, 100000)
        # initialise RTC chip
        self.rtc = PCF85063A(self.i2c)
        self.i2c.writeto_mem(0x51, 0x00, b"\x00")
        self.rtc.enable_timer_interrupt(False)
        t = self.rtc.datetime()
        # sync pico's RTC to chip
        RTC().datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))
        self.activity_led = ActivityLED()
