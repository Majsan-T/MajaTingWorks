# app/blog/utils.py
from flask_mail import Message
from flask import current_app, url_for
from app.models import User, BlogPost, db, Role
from app.extensions import mail
from datetime import datetime, timezone

# ======================
# ✅ HANTERA BLOGGMAIL
# ======================

def check_and_send_blog_emails():
    """
    Kontrollera publicerade inlägg som ännu inte skickats ut via e-post
    och skicka max 10 st åt gången.
    """
    now = datetime.now(timezone.utc)
    MAX_EMAILS = 10

    # ✅ Hämta inlägg som är publicerade men inte skickade
    pending_posts = BlogPost.query.filter(
        BlogPost.created_at <= now,
        BlogPost.email_sent == False
    ).limit(MAX_EMAILS).all()

    current_app.logger.info(f"Hittade {len(pending_posts)} inlägg att skicka ut.")

    for post in pending_posts:
        try:
            notify_subscribers(post)  # ✅ Skicka mail till alla prenumeranter
            post.email_sent = True
            db.session.commit()  # Kommitta efter varje lyckat utskick
        except Exception as e:
            current_app.logger.error(f"❌ Misslyckades skicka mail för post {post.id}: {e}")
            db.session.rollback()


def notify_subscribers(post):
    """
    Skicka mail om nytt blogginlägg till alla prenumeranter.
    Om inga prenumeranter finns avslutas funktionen direkt.
    """
    from app.extensions import mail  # ✅ För att undvika cirkulär import

    subscribers = User.query.join(User.roles).filter(Role.name == "subscriber").all()
    if not subscribers:
        return

    for subscriber in subscribers:
        try:
            msg = Message(
                subject=f"Nytt blogginlägg: {post.title}",
                sender=current_app.config["MAIL_DEFAULT_SENDER"],
                recipients=[subscriber.email]
            )
            msg.body = f"""
Hej {subscriber.name},

Ett nytt blogginlägg har publicerats: {post.title}

{post.subtitle}

Läs mer här:
{url_for('blog.show_post', post_id=post.id, _external=True)}

Hälsningar,
Maria Tingvall
"""
            mail.send(msg)
        except Exception as e:
            current_app.logger.warning(f"⚠️ Kunde inte skicka mail till {subscriber.email}: {e}")
