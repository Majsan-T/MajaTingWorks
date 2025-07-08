# i t.ex. app/utils/filters.py
from markupsafe import Markup, escape
from babel.dates import format_datetime
from datetime import datetime
from app.utils.time import DEFAULT_TZ
import pytz

def nl2br(value):
    """Escape:a text och ersätt newline med <br>."""
    if value is None:
        return ""
    escaped = escape(value)
    return Markup( "<br>".join(escaped.splitlines()) )

def format_datetime_sv(dt, fmt="EEEE d MMMM y 'kl.' HH:mm"):
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    local_dt = dt.astimezone(pytz.timezone("Europe/Stockholm"))
    return format_datetime(local_dt, format=fmt, locale="sv_SE")
