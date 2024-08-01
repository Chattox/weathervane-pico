from machine import PWM, Pin
from constants import ACTIVITY_LED_PIN


class ActivityLED:
    """
    Controls the activity LED on the enviro board
    """

    def __init__(self):
        self._act_led_pwm = PWM(Pin(ACTIVITY_LED_PIN))
        self._act_led_pwm.freq(1000)
        self._act_led_pwm.duty_u16(0)

    def set_brightness(self, level):
        """
        Set the brightness of the activity LED

        Parameters
        ----------
        level : int
            Target brightness level ideally from 0 - 100
        """
        # clamp to within range
        brightness = max(0, min(100, level))
        # gamma correction (gamma 2.8)
        b_val = int(pow(brightness / 100.0, 2.8) * 65535.0 + 0.5)
        self._act_led_pwm.duty_u16(b_val)
