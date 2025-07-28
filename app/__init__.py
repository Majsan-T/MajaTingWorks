# app/__init__.py
import os
import logging
import click
from datetime import datetime, timezone
from config import DevelopmentConfig, ProductionConfig

from flask import Flask, render_template, current_app, request
from flask.cli import with_appcontext
from flask_bootstrap import Bootstrap5
from flask_babel import Babel, format_datetime, gettext as _, ngettext
from flask_wtf.csrf import CSRFError
from werkzeug.security import generate_password_hash

from app.extensions import db, login_manager, mail, csrf, migrate, babel
from app.utils.filters import nl2br, format_datetime_sv
from app.utils.helpers import strip_and_truncate, linebreaks
from app.models import User, BlogPost, BlogCategory, Comment, PortfolioItem, Category, Role
from app.cli import fix_post_timestamps, reset_bad_updated_at, register_cli_commands

# from app.blog.utils import check_and_send_blog_emails

# 📁 Hitta basmapp för statiska filer och mallar
base_dir = os.path.abspath(os.path.dirname(__file__))

babel = Babel()


# ======================
# ✅ CLI-KOMMANDON
# ======================

@click.command("roles-setup")
@with_appcontext
def roles_setup():
    """Skapa standardroller (user, subscriber, admin) – körs vid första setup."""
    default_roles = ["user", "subscriber", "admin"]
    created = []
    for role_name in default_roles:
        if not Role.query.filter_by(name=role_name).first():
            db.session.add(Role(name=role_name))
            created.append(role_name)
    db.session.commit()

    if created:
        click.echo(f"✅ Skapade roller: {', '.join(created)}")
    else:
        click.echo("ℹ️ Alla roller finns redan.")


@click.command("make-admin")
@with_appcontext
def make_admin():
    """Gör en befintlig användare till admin (via CLI)."""
    email = input("Ange användarens e-post: ").strip()
    user = User.query.filter_by(email=email).first()
    if not user:
        click.echo("❌ Ingen användare hittades.")
        return
    user.add_role("admin")
    db.session.commit()
    click.echo(f"✅ {email} är nu admin!")


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
    register_cli_commands(app)

    # ✅ Registrera Blueprints
    from app.admin.admin import admin_bp
    from app.auth.routes import auth_bp
    from app.blog.blog import blog_bp
    from app.blog.cli import send_blog_mails
    from app.pages.pages import pages_bp
    from app.portfolio.portfolio import portfolio_bp

    app.cli.add_command(fix_post_timestamps)
    app.cli.add_command(reset_bad_updated_at)
    app.cli.add_command(send_blog_mails)
    app.cli.add_command(roles_setup)
    app.cli.add_command(make_admin)

    app.register_blueprint(blog_bp, url_prefix='/blog')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(pages_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(portfolio_bp, url_prefix='/portfolio')

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

    # ✅ CLI: skapa adminanvändare via terminal
    @app.cli.command("create-admin")
    def create_admin():
        """Skapa en adminanvändare via kommandoraden (ej via GUI)."""
        from app.models import User
        from app.extensions import db

        email = input("E-postadress: ").strip()
        name = input("Namn: ").strip()
        password = input("Lösenord: ").strip()

        if not email or not password:
            print("❌ E-post och lösenord krävs.")
            return

        if User.query.filter_by(email=email).first():
            print("⚠️ En användare med den e-postadressen finns redan.")
            return

        hashed_password = generate_password_hash(password)

        new_admin = User(
            email=email,
            name=name,
            password=hashed_password,
            role="admin"
        )
        db.session.add(new_admin)
        db.session.commit()
        print("✅ Adminanvändare skapad!")

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
