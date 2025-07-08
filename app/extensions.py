# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from flask_babel import Babel

csrf = CSRFProtect()
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
babel = Babel()