from machine import PWM, Pin, Timer
from math import sin, pi
from time import ticks_ms
from utils.constants import ACTIVITY_LED_PIN


class ActivityLED:
    """
    Controls the activity LED on the enviro board
    """

    def __init__(self):
        self.__pwm = PWM(Pin(ACTIVITY_LED_PIN))
        self.__pwm.freq(1000)
        self.__pwm.duty_u16(0)
        self.__timer = Timer(-1)
        self.__pulse_speed_hz = 1

    def set_brightness(self, level):
        """
        Set the brightness of the activity LED

        Args:
            level (int): Target brightness level between 0 - 100
        """
        # clamp to within range
        brightness = max(0, min(100, level))
        # gamma correction (gamma 2.8)
        b_val = int(pow(brightness / 100.0, 2.8) * 65535.0 + 0.5)
        self.__pwm.duty_u16(b_val)

    def __pulse_callback(self, t):
        """
        Updates the activity LED brightness based on a sinusoid seeded by the current time

        Args:
            t (Timer): The Timer object passed as part of the Timer callback
        """
        brightness = (
            sin(ticks_ms() * pi * 2 / (1000 / self.__pulse_speed_hz)) * 40
        ) + 60
        b_val = int(pow(brightness / 100.0, 2.8) * 65535.0 + 0.5)
        self.__pwm.duty_u16(b_val)

    def pulse(self, speed_hz=1):
        """
        Pulses the activity LED

        Args:
            speed_hz (int): Speed of the LED pulse in Hz
        """
        self.__pulse_speed_hz = speed_hz
        self.__timer.deinit()
        self.__timer.init(
            period=50, mode=Timer.PERIODIC, callback=self.__pulse_callback
        )

    def stop(self):
        """
        Turns off the activity LED and stops any pulse animations currently running
        """
        self.__timer.deinit()
        self.__pwm.duty_u16(0)
