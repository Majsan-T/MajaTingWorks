from flask_apscheduler import APScheduler
from datetime import datetime
from flask import current_app
from app.blog.utils import check_and_send_blog_emails

scheduler = APScheduler()

def scheduled_blog_emails():
    """Körs en gång om dagen och skickar mail för max 10 inlägg."""
    current_app.logger.info(f"📬 Schemalagd körning startad: {datetime.now()}")
    try:
        check_and_send_blog_emails()
        current_app.logger.info("✅ Schemalagd körning klar utan fel.")
    except Exception as e:
        current_app.logger.error(f"❌ Fel vid schemalagd körning: {e}")

def init_scheduler(app):
    """Initiera och starta schemaläggaren."""
    scheduler.init_app(app)
    scheduler.start()

    # Lägg till jobb som körs en gång per dag kl 08:00
    scheduler.add_job(
        id="daily_blog_emails",
        func=scheduled_blog_emails,
        trigger="cron",
        hour=21,  # kl 08:00 varje dag
        minute=0
    )
