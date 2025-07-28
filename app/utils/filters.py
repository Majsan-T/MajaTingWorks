# app/utils/filters.py
from markupsafe import Markup, escape
from babel.dates import format_datetime
from datetime import datetime
from app.utils.time import DEFAULT_TZ
import pytz

# ===================================================
# ✅ Egna Jinja-filter för templates
# ===================================================

def nl2br(value):
    """
    ✅ Konverterar newlines (\n) till <br> för HTML.
    - Escape:ar först texten så att farlig HTML inte körs.
    - Används i Jinja-templates för att visa radbrytningar korrekt.
    """
    if value is None:
        return ""
    escaped = escape(value)
    return Markup("<br>".join(escaped.splitlines()))


def format_datetime_sv(dt, fmt="EEEE d MMMM y 'kl.' HH:mm"):
    """
    ✅ Formaterar ett datetime-objekt till svenskt format.
    - Om dt saknar tidszon: sätts till UTC först.
    - Konverteras sedan till Europe/Stockholm.
    - Standardformat: 'måndag 3 juni 2025 kl. 14:30'.
    - Används i templates via |format_datetime_sv.
    """
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    local_dt = dt.astimezone(pytz.timezone("Europe/Stockholm"))
    return format_datetime(local_dt, format=fmt, locale="sv_SE")

