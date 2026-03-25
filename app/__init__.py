# app/__init__.py
import os
import logging
from datetime import datetime, timezone
from config import DevelopmentConfig, ProductionConfig

from flask import Flask, render_template, current_app, request
from flask_bootstrap import Bootstrap5
from flask_babel import Babel
from flask_wtf.csrf import CSRFError

from app.extensions import db, login_manager, mail, csrf, migrate, babel
from app.utils.filters import nl2br, format_datetime_sv
from app.utils.helpers import strip_and_truncate, linebreaks

# 📁 Hitta basmapp för statiska filer och mallar
base_dir = os.path.abspath(os.path.dirname(__file__))

babel = Babel()


# ======================
# ✅ HUVUDFUNKTION – skapa app
# ======================

def create_app():
    """Skapar och konfigurerar Flask-appen."""
    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, '..', 'static'),
        template_folder=os.path.join(base_dir, '..', 'templates')
    )

    # ✅ Loggning (endast i produktion)
    if not app.debug and not app.testing:
        file_handler = logging.FileHandler("runtime.log")
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    # ✅ Välj konfiguration beroende på miljö
    if os.getenv("FLASK_ENV") == "development":
        app.config.from_object(DevelopmentConfig)
    else:
        app.config.from_object(ProductionConfig)

    # ✅ Initiera extensions
    db.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app, locale_selector=lambda: 'sv', timezone_selector=lambda: 'Europe/Stockholm')
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    Bootstrap5(app)

    # ✅ Registrera Blueprints
    from app.admin.admin import admin_bp
    from app.auth.routes import auth_bp
    from app.blog.blog import blog_bp
    from app.pages.pages import pages_bp
    from app.portfolio.portfolio import portfolio_bp

    app.register_blueprint(blog_bp, url_prefix='/blog')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(pages_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(portfolio_bp, url_prefix='/portfolio')

    # ✅ Registrera CLI-kommandon
    from app.cli import create_admin, reset_stats, aggregate_stats
    app.cli.add_command(create_admin)
    app.cli.add_command(reset_stats)
    app.cli.add_command(aggregate_stats)
    
    # ✅ Registrera CLI-kommandon från app/blog/cli.py
    from app.blog.cli import send_blog_mails
    app.cli.add_command(send_blog_mails)
    
    # ✅ Jinja-filter (globala)
    app.jinja_env.filters['strip_and_truncate'] = strip_and_truncate
    app.jinja_env.filters['linebreaks'] = linebreaks
    app.jinja_env.filters['nl2br'] = nl2br
    app.jinja_env.filters['format_datetime_sv'] = format_datetime_sv

    # ✅ Globala variabler – tillgängliga i alla templates
    @app.context_processor
    def inject_global_variables():
        """Lägg till 'year', 'datetime' och 'timezone' i alla mallar."""
        return {
            'year': datetime.now().year,
            'datetime': datetime,
            'timezone': timezone
        }

    # ✅ CSRF-felhantering
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """Fångar CSRF-fel och visar anpassad sida."""
        return render_template('errors/csrf_error.html', reason=e.description), 400

    # ======================
    # ✅ GLOBALA FELHANTERARE
    # ======================

    @app.errorhandler(403)
    def forbidden_error(error):
        """403 – Åtkomst nekad."""
        current_app.logger.warning(f"Global 403 Forbidden caught: {error}")
        return render_template('admin/403.html'), 403

    @app.errorhandler(413)
    def request_entity_too_large(error):
        """413 – Uppladdad fil för stor."""
        current_app.logger.warning(f"Global 413 Request Entity Too Large caught: {error}")
        return render_template('errors/413.html'), 413

    @app.errorhandler(404)
    def page_not_found(e):
        """404 – Sidan hittades inte."""
        current_app.logger.warning(f"404: {request.path} not found.")
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """500 – Allvarligt serverfel."""
        try:
            db.session.rollback()
        except Exception as e:
            current_app.logger.error(f"Failed to rollback DB session during 500 error: {e}")

        current_app.logger.error(f"Global 500 Internal Server Error caught: {error}", exc_info=True)
        return render_template('errors/500.html'), 500
    

    return app