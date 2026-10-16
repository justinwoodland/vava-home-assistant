DOMAIN = "vava_projector"
DEFAULT_HTTP_PORT = 8000
DEFAULT_TCP_PORT = 8121
DEFAULT_POLL_INTERVAL = 10  # seconds
DEFAULT_SHUTDOWN_GRACE = 15  # seconds
HTTP_POWER_KEYCODE = 26  # Android KEYCODE_POWER fallback

KEYCODES = {
    "POWER": 203,
    "UP": 19,
    "DOWN": 20,
    "LEFT": 21,
    "RIGHT": 22,
    "OK": 66,
    "BACK": 4,
    "HOME": 3,
    "MENU": 82,
    "VOLUME_UP": 24,
    "VOLUME_DOWN": 25,
}

CONF_HOST = "host"
CONF_HTTP_PORT = "http_port"
CONF_TCP_PORT = "tcp_port"
CONF_POLL_INTERVAL = "poll_interval"
CONF_SHUTDOWN_GRACE = "shutdown_grace"
