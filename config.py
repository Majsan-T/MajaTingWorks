# config.py

import os
from zoneinfo import ZoneInfo


class Config:
    # Miljö
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    ENV = FLASK_ENV  # Flask använder både ENV och FLASK_ENV ibland
    DEBUG = FLASK_ENV == "development"

    # Säkerhet
    SECRET_KEY = os.getenv("SECRET_KEY", "your_strong_default_dev_secret_key_here")

    # Databas
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///site.db") if DEBUG else os.getenv("DATABASE_URL")

    # Uploads
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    UPLOAD_FOLDER = "uploads"
    TZ = ZoneInfo("Europe/Stockholm")

    # Språkstöd
    LANGUAGES = ["en", "sv"]
    BABEL_DEFAULT_LOCALE = "sv"

    # CaptchaFox
    CAPTCHAFOX_SITE_KEY = os.getenv("CAPTCHAFOX_SITE_KEY")
    CAPTCHAFOX_SECRET_KEY = os.getenv("CAPTCHAFOX_SECRET_KEY")

    # E-post
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")


class DevelopmentConfig(Config):
    FLASK_ENV = "development"
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///site.db")


class ProductionConfig(Config):
    FLASK_ENV = "production"
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")


def get_config():
    env = os.getenv("FLASK_ENV", "production").lower()

    if env == "development":
        return DevelopmentConfig
    else:
        # 🟡 Tillåt SQLite-fallback vid CLI-användning
        if os.getenv("FLASK_CLI") == "true" and not os.getenv("DATABASE_URL"):
            class TemporaryConfig(ProductionConfig):
                SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
            return TemporaryConfig

        return ProductionConfig
