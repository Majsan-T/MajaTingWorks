# app/utils/time.py
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

# ✅ Standardtidszon för hela applikationen
DEFAULT_TZ = ZoneInfo("Europe/Stockholm")
UTC_TZ = ZoneInfo("UTC")


def get_local_now() -> datetime:
    """
    ✅ Returnerar aktuell tid i Stockholm som UTC (för databas).
    
    VIKTIGT: Databasen ska ALLTID spara i UTC.
    Detta returnerar nuvarande Stockholmstid konverterad till UTC.
    """
    return datetime.now(UTC_TZ)


def get_display_time(dt: Optional[datetime] = None) -> datetime:
    """
    ✅ Konverterar UTC-tid från databas till Stockholmstid för visning.
    
    Args:
        dt: UTC datetime från databas (eller None för nuvarande tid)
    
    Returns:
        Datetime i Stockholm-tidszon
    """
    if dt is None:
        return datetime.now(DEFAULT_TZ)
    
    # Om naive datetime - anta att det är UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)
    
    return dt.astimezone(DEFAULT_TZ)


def parse_form_datetime(date_str: str, time_str: str) -> datetime:
    """
    ✅ Konverterar datum + tid från formulär till UTC för databas.
    
    Args:
        date_str: Datum från formulär (YYYY-MM-DD)
        time_str: Tid från formulär (HH:MM)
    
    Returns:
        UTC datetime redo för databas
    """
    # Kombinera datum och tid
    naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    
    # Lokalisera till Stockholm
    stockholm_dt = naive_dt.replace(tzinfo=DEFAULT_TZ)
    
    # Konvertera till UTC
    return stockholm_dt.astimezone(UTC_TZ)


def get_timezone() -> ZoneInfo:
    """
    ✅ Returnerar tzinfo-objekt för Europe/Stockholm.
    """
    return DEFAULT_TZ