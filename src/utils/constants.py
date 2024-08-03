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

# Wifi constants
# Connection statuses
CYW43_LINK_DOWN = 0
CYW43_LINK_JOIN = 1
CYW43_LINK_NOIP = 2
CYW43_LINK_UP = 3
CYW43_LINK_FAIL = -1
CYW43_LINK_NONET = -2
CYW43_LINK_BADAUTH = -3

# Connection status names
CYW43_STATUS_NAMES = {
    CYW43_LINK_DOWN: "Link is down",
    CYW43_LINK_JOIN: "Connected to wifi",
    CYW43_LINK_NOIP: "Connected to wifi, but no IP address",
    CYW43_LINK_UP: "Connected to wifi, with IP address",
    CYW43_LINK_FAIL: "Connection failed",
    CYW43_LINK_NONET: "No matching SSID found (could be out of range, or down)",
    CYW43_LINK_BADAUTH: "Authentication failure",
}

# Other helpful values
# Distance from the centre of the anemometer to the
# centre of one of the cups in cm
WIND_RADIUS_CM = 7.0
# Scaling factor for wind speed in m/s
WIND_FACTOR = 0.0218
# Amount of rain required for the bucket sensor to tip in mm
RAIN_MM_PER_TICK = 0.2794
