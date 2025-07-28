# app/utils/time.py
from datetime import datetime
from zoneinfo import ZoneInfo

# ✅ Standardtidszon för hela applikationen
DEFAULT_TZ = ZoneInfo("Europe/Stockholm")


def get_local_now():
    """
    ✅ Returnerar aktuell lokaltid i Stockholm.
    - Returneras som **naive datetime** (ingen tzinfo) eftersom MySQL oftast hanterar datetider utan tidszonsinfo.
    - Används när du sparar i databasen men vill att tiden ska vara lokal svensk tid.
    """
    local_time = datetime.now(ZoneInfo("Europe/Stockholm"))
    return local_time.replace(tzinfo=None)


def get_timezone() -> ZoneInfo:
    """
    ✅ Returnerar tzinfo-objekt för Europe/Stockholm.
    - Används vid konvertering mellan tidszoner eller när du explicit vill ha tidszonsmedvetna tider.
    """
    return DEFAULT_TZ

