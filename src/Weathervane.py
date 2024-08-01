from machine import Pin, RTC
from pimoroni_i2c import PimoroniI2C
from pcf85063a import PCF85063A
from wakeup import get_gpio_state
from utils.constants import (
    BUTTON_PIN,
    I2C_SDA_PIN,
    I2C_SCL_PIN,
    RAIN_PIN,
    RTC_ALARM_PIN,
    WAKE_BUTTON_PRESS,
    WAKE_RAIN_TRIGGER,
    WAKE_REASON_NAMES,
    WAKE_RTC_ALARM,
    WAKE_USB_POWERED,
)
from Logging import Logging
from ActivityLED import ActivityLED


class Weathervane:
    """
    Handles overall functionality of the enviro board

    Attributes:
        rtc (PCF85063A): controller for RTC chip
        activity_led (ActivityLED): controller for activity LED
    """

    def __init__(self):
        self.logger = Logging()
        # state of vbus to know if woken by USB
        self.__vbus_present = Pin("WL_GPIO2", Pin.IN).value()
        self.__i2c = PimoroniI2C(I2C_SDA_PIN, I2C_SCL_PIN, 100000)
        # initialise RTC chip
        self.rtc = PCF85063A(self.__i2c)
        self.__i2c.writeto_mem(0x51, 0x00, b"\x00")
        self.rtc.enable_timer_interrupt(False)
        t = self.rtc.datetime()
        # sync pico's RTC to chip
        RTC().datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))
        self.activity_led = ActivityLED()

    def startup(self):
        """
        Startup process.

        - Get reason for waking
        - If rain, cache reading and sleep
        - Else, continue with wake process

        Returns:
            bool: True if wake not rain triggered
        """
        self.logger.info("Starting up...")

        reason = self.get_wake_reason()
        self.logger.info(" - Wake reason: ", WAKE_REASON_NAMES[reason])

    def get_wake_reason(self):
        """
        Get reason for waking

        Returns:
            int: wake reason constant
        """
        wake_reason = None
        gpio_state = get_gpio_state()

        if gpio_state & (1 << BUTTON_PIN):
            wake_reason = WAKE_BUTTON_PRESS
        elif gpio_state & (1 << RTC_ALARM_PIN):
            wake_reason = WAKE_RTC_ALARM
        elif gpio_state & (1 << RAIN_PIN):
            wake_reason = WAKE_RAIN_TRIGGER
        elif self.__vbus_present:
            wake_reason = WAKE_USB_POWERED

        return wake_reason
