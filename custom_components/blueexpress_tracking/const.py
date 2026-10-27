"""Constants for the unofficial Blue Express tracking integration."""

from datetime import timedelta

DOMAIN = "blueexpress_tracking"
CONF_TRACKING_NUMBER = "tracking_number"
CONF_LABEL = "label"
DEFAULT_INTERVAL = timedelta(minutes=30)
TRACKING_URL = "https://www.blue.cl/enviar/seguimiento?n_seguimiento={}"
API_BASE = "https://www.blue.cl/api"
MAX_HISTORY = 70
