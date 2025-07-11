# app/__init__.py
import os
import logging
import click
from datetime import datetime, timezone
from config import DevelopmentConfig, ProductionConfig

from flask import Flask, render_template, current_app, request
from flask_bootstrap import Bootstrap5
from flask_babel import Babel, format_datetime, gettext as _, ngettext
from flask_wtf.csrf import CSRFError
from werkzeug.security import generate_password_hash
from apscheduler.schedulers.background import BackgroundScheduler

from app.extensions import db, login_manager, mail, csrf, migrate, babel
from app.utils.filters import nl2br, format_datetime_sv
from app.utils.helpers import strip_and_truncate, linebreaks
from app.models import User, BlogPost, BlogCategory, Comment, PortfolioItem, Category
from app.cli import fix_post_timestamps, reset_bad_updated_at, register_cli_commands
from app.blog.scheduler import check_and_notify_posts
from app.blog.utils import check_and_send_blog_emails

# 📁 Hitta basmapp för statisk och mallar
base_dir = os.path.abspath(os.path.dirname(__file__))

babel = Babel()

def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, '..', 'static'),
        template_folder=os.path.join(base_dir, '..', 'templates')
    )

    if os.getenv("FLASK_ENV") == "development":
        app.config.from_object(DevelopmentConfig)
    else:
        app.config.from_object(ProductionConfig)

    # 🔧 Initiera extensions
    db.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app, locale_selector=lambda: 'sv', timezone_selector=lambda: 'Europe/Stockholm')
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    Bootstrap5(app)
    register_cli_commands(app)

    # 🔗 Registrera Blueprints
    from app.admin.admin import admin_bp
    from app.auth.auth import auth_bp
    from app.blog.blog import blog_bp
    from app.blog.cli import send_blog_mails
    from app.pages.pages import pages_bp
    from app.portfolio.portfolio import portfolio_bp

    app.cli.add_command(fix_post_timestamps)
    app.cli.add_command(reset_bad_updated_at)
    app.cli.add_command(send_blog_mails)

    app.register_blueprint(blog_bp, url_prefix='/blog')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(pages_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(portfolio_bp, url_prefix='/portfolio')

    # 🧠 Globala Jinja-filter
    app.jinja_env.filters['strip_and_truncate'] = strip_and_truncate
    app.jinja_env.filters['linebreaks'] = linebreaks
    app.jinja_env.filters['nl2br'] = nl2br
    app.jinja_env.filters['format_datetime_sv'] = format_datetime_sv

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_and_notify_posts, trigger="interval", minutes=30)
    scheduler.start()

    # 📆 Global variabel "year" till alla templates
    @app.context_processor
    def inject_global_variables():
        return {
            'year': datetime.now().year,
            'datetime': datetime,
            'timezone': timezone
        }

    # 🛡️ CSRF-felhantering
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/csrf_error.html', reason=e.description), 400
        
    @app.cli.command("create-admin")
    def create_admin():
        """Skapa en adminanvändare via kommandoraden."""
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

    # === GLOBALA FELHANTERARE ===
    # 403 - Forbidden
    @app.errorhandler(403)
    def forbidden_error(error):
        current_app.logger.warning(f"Global 403 Forbidden caught: {error}")
        return render_template('admin/403.html'), 403
    # 413 - Request Entity Too Large
    @app.errorhandler(413)
    def request_entity_too_large(error):
        current_app.logger.warning(f"Global 413 Request Entity Too Large caught: {error}")
        return render_template('errors/413.html'), 413 # Eller 'admin/413.html' om du vill
    # 404 - Not Found
    @app.errorhandler(404)
    def page_not_found(error):
        current_app.logger.warning(f"Global 404 Not Found caught: {error}")
        return render_template('errors/404.html'), 404
    # 500 - Internal Server Error
    @app.errorhandler(500)
    def internal_error(error):
        try:
            db.session.rollback()
        except Exception as e:
            current_app.logger.error(f"Failed to rollback DB session during 500 error: {e}")

        current_app.logger.error(f"Global 500 Internal Server Error caught: {error}", exc_info=True)
        return render_template('errors/500.html'), 500
    # ============================
    
    # Endast i utvecklingsmiljö
    if app.config.get("FLASK_ENV") == "development":
        @app.cli.command("db-reset")
        def reset_db():
            """Rensar databasen och skapar alla tabeller på nytt."""
            from app.models import db, User
            click.confirm("⚠️  Detta kommer radera ALLA tabeller. Vill du fortsätta?", abort=True)
            with app.app_context():
                db.drop_all()
                db.create_all()
                click.echo("✅ Databasen har återställts.")

                # Skapa admin-användare
                admin = User(
                    email=os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com"),
                    password=generate_password_hash(os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")),
                    name="Maria",
                    role="admin"
                )
                db.session.add(admin)
                db.session.commit()
                click.echo("👤 Admin-användare skapad: admin@example.com / admin")

    from app.blog.cli import send_blog_mails
    app.cli.add_command(send_blog_mails)

    # Stoppa schemaläggaren vid app shutdown
    import atexit
    atexit.register(lambda: scheduler.shutdown(wait=False))

    return app
