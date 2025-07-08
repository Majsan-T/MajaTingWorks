# config.py

import os
from zoneinfo import ZoneInfo

class Config:
    # SECRET_KEY och FLASK_ENV ska läsas från miljövariabler HÄR!
    SECRET_KEY = os.getenv("SECRET_KEY", "your_strong_default_dev_secret_key_here")
    FLASK_ENV = os.getenv("FLASK_ENV", "production") # Sätt denna till production på Oderland

    # SQLALCHEMY_DATABASE_URI ska ENBART läsas från DATABASE_URL här
    # Ta bort alla gamla DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
    # om du använder en DATABASE_URL-sträng
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    # Om SQLALCHEMY_DATABASE_URI ÄR tom (t.ex. vid lokal utveckling utan .env)
    # kan du sätta en fallback här, eller låta den krascha tidigt lokalt om det saknas.
    if not SQLALCHEMY_DATABASE_URI:
        # Detta är för din LOKALA utveckling, om du INTE har DATABASE_URL i din .env
        # och vill använda SQLite lokalt.
        SQLALCHEMY_DATABASE_URI = "sqlite:///site.db" # Eller din lokala MySQL-anslutning

    SQLALCHEMY_TRACK_MODIFICATIONS = False # Bra att ha med
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    UPLOAD_FOLDER = 'uploads'
    TZ = ZoneInfo("Europe/Stockholm")

    # Localization
    LANGUAGES = ["en", "sv"]
    BABEL_DEFAULT_LOCALE = "sv"

    # CaptchaFox (läs från env här)
    CAPTCHAFOX_SITE_KEY = os.getenv("CAPTCHAFOX_SITE_KEY")
    CAPTCHAFOX_SECRET_KEY = os.getenv("CAPTCHAFOX_SECRET_KEY")

    # E-post (läs från env här)
    MAIL_SERVER = os.getenv("MAIL_SERVER", 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    if not SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI = "sqlite:///site.db"