# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from flask_babel import Babel

# ===================================================
# ✅ Flask-extensions initieras här
# ===================================================
# Dessa objekt initieras här och kopplas sedan till appen
# i create_app() i app/__init__.py

# 🛡️ CSRF-skydd – förhindrar Cross-Site Request Forgery-attacker
csrf = CSRFProtect()

# 🗄️ Databashantering via SQLAlchemy
db = SQLAlchemy()

# 🔑 Inloggningshantering för Flask-login
login_manager = LoginManager()

# 📧 E-postfunktioner (Flask-Mail)
mail = Mail()

# 🔄 Databasmigreringar (Alembic via Flask-Migrate)
migrate = Migrate()

# 🌍 Internationellt stöd (översättningar, datumformat)
babel = Babel()
