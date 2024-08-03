from machine import Pin, RTC, idle, reset
from time import sleep_ms
from pimoroni_i2c import PimoroniI2C
from pcf85063a import PCF85063A
from wakeup import get_gpio_state
from utils.config import reading_frequency
from utils.constants import (
    BUTTON_PIN,
    HOLD_VSYS_EN_PIN,
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
from Sensors import Sensors


class Weathervane:
    """
    Handles overall functionality of the enviro board

    Attributes:
        logger (Logging): Logger for saving log output to file
        button (Pin): The button on the front of the enviro itself
        rtc (PCF85063A): Controller for RTC chip
        activity_led (ActivityLED): Controller for activity LED
        sensors (Sensors): For getting sensor data
    """

    def __init__(self):
        # Hold VSYS_EN pin high to keep power to the board when on battery
        self.__hold_vsys_en_pin = Pin(HOLD_VSYS_EN_PIN, Pin.OUT, value=True)
        self.logger = Logging()
        self.button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
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
        self.sensors = Sensors(self.logger, self.__i2c, self.activity_led)

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

        reason = self.__get_wake_reason()
        self.logger.info(" - Wake reason: ", WAKE_REASON_NAMES[reason])

        # If woken by rain trigger, log and go back to sleep
        if reason == WAKE_RAIN_TRIGGER:
            self.sensors.check_rain_sensor(True)
            self.sleep()

        # Pulse activity LED to show board is active
        self.activity_led.pulse()

    def __get_wake_reason(self):
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

    def sleep(self):
        """
        Puts the enviro board into a sleep state by cutting power to the pico W.

        If on USB power, this will have no effect and so the board will instead go
        into a monitoring state awaiting the next trigger
        """
        self.logger.info("Going to sleep")

        # Clear RTC flags
        self.rtc.clear_alarm_flag()
        self.rtc.clear_timer_flag()

        # Set alarm for next scheduled reading
        dt = self.rtc.datetime()
        hour, minute, second = dt[3:6]

        # Figure out what time the next reading should be at
        minute += reading_frequency - (minute % reading_frequency)
        if minute >= 60:
            hour += 1
            minute -= 60
        if hour >= 24:
            hour -= 24

        self.logger.info(f"- Setting alarm to wake at {hour:02}:{minute:02}")

        # Set RTC alarm
        self.rtc.set_alarm(0, minute, hour)
        self.rtc.enable_alarm_interrupt(True)

        # Disable VSYS hold, cutting power to the pico (if on battery)
        self.logger.info("- Shutting down (if on battery)")
        self.__hold_vsys_en_pin.init(Pin.IN)

        # If this code is reached it means power is coming from USB
        # instead of battery so the board can't (and doesn't need to) go to sleep
        self.activity_led.stop()

        self.logger.info(
            "- On USB power so can't shut down. Waiting for alarm or other trigger instead"
        )
        while not self.rtc.read_alarm_flag():
            self.sensors.check_rain_sensor()
            sleep_ms(1)
            # Reset on button press
            if self.button.value():
                self.logger.info("- Button pressed, resetting board")
                break

        reset()
