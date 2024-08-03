# System pins
HOLD_VSYS_EN_PIN = 2
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
WIFI_CS_PIN = 25

# Sensor pins
EXTERNAL_INTERRUPT_PIN = 3
ACTIVITY_LED_PIN = 6
BUTTON_PIN = 7
RTC_ALARM_PIN = 8
WIND_SPEED_PIN = 9
RAIN_PIN = 10
WIND_DIR_PIN = 26

# Wake reasons
WAKE_UNKNOWN = None
WAKE_BUTTON_PRESS = 2
WAKE_RTC_ALARM = 3
WAKE_EXT_TRIGGER = 4
WAKE_RAIN_TRIGGER = 5
WAKE_USB_POWERED = 6

# Warn LED states
WARN_LED_OFF = 0
WARN_LED_ON = 1
WARN_LED_BLINK = 2

# Wake reasons as strings for logging
WAKE_REASON_NAMES = {
    None: "Unknown",
    WAKE_BUTTON_PRESS: "Button",
    WAKE_RTC_ALARM: "RTC Alarm",
    WAKE_EXT_TRIGGER: "External trigger",
    WAKE_RAIN_TRIGGER: "Rain trigger",
    WAKE_USB_POWERED: "USB powered",
}

# Other helpful values
# Distance from the centre of the anemometer to the
# centre of one of the cups in cm
WIND_RADIUS_CM = 7.0
# Scaling factor for wind speed in m/s
WIND_FACTOR = 0.0218
# Amount of rain required for the bucket sensor to tip in mm
RAIN_MM_PER_TICK = 0.2794
