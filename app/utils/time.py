# app/utils/time.py

from datetime import datetime
from zoneinfo import ZoneInfo

DEFAULT_TZ = ZoneInfo("Europe/Stockholm")

def get_local_now() -> datetime:
    """Returnerar aktuell tid med Europe/Stockholm som tzinfo."""
    return datetime.now(DEFAULT_TZ)

def get_timezone() -> ZoneInfo:
    """Returnerar tzinfo-objekt för Europe/Stockholm."""
    return DEFAULT_TZ
