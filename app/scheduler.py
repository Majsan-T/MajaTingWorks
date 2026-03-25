# app/scheduler.py
"""
✅ Automatisk schemaläggare för bloggmail
✅ Körs var 15:e minut inuti Flask-appen
✅ Ingen cron/cronjob behövs!

Använder APScheduler för att köra check_and_send_blog_emails()
regelbundet i bakgrunden.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import logging

logger = logging.getLogger(__name__)

def start_scheduler(app):
    """
    Startar bakgrundsschedulern när Flask-appen startar.
    
    Args:
        app: Flask application instance
    
    Körs automatiskt var 15:e minut och stoppar när appen stängs.
    """
    
    # Skapa scheduler (daemon=True betyder att den körs i bakgrunden)
    scheduler = BackgroundScheduler(daemon=True)
    
    # Lägg till jobb: skicka bloggmail var 15:e minut
    scheduler.add_job(
        func=lambda: send_emails_job(app),
        trigger=IntervalTrigger(minutes=15),
        id='send_blog_emails',
        name='Skicka bloggmail till prenumeranter',
        replace_existing=True,
        max_instances=1  # Förhindrar att flera instanser körs samtidigt
    )
    
    # Starta schedulern
    scheduler.start()
    logger.info("📧 Bloggmail-scheduler startad! Körs var 15:e minut.")
    
    # Stoppa schedulern när Flask-appen stängs
    atexit.register(lambda: scheduler.shutdown(wait=False))


def send_emails_job(app):
    """
    Jobbet som körs var 15:e minut.
    
    Kör check_and_send_blog_emails() i Flask app-context
    så att databaskopplingar och konfiguration fungerar.
    """
    with app.app_context():
        try:
            # Importera funktionen (undvik cirkulär import)
            from app.blog.utils import check_and_send_blog_emails
            
            logger.info("🤖 AUTOMATISK mailkörning startad (scheduler)")
            
            # Kör mailutskicket
            check_and_send_blog_emails()
            
        except Exception as e:
            logger.error(f"❌ Scheduler-fel vid mailutskick: {e}", exc_info=True)