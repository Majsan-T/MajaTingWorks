# app/blog/utils.py
from flask_mail import Message
from flask import current_app, url_for
from app.models import User, BlogPost, db, Role
from app.extensions import mail
from datetime import datetime, timezone

def check_and_send_blog_emails():
    """
    ✅ OPTIMERAD: Skickar max 10 mail åt gången med bättre felhantering
    """
    now = datetime.now(timezone.utc)
    MAX_EMAILS = 10

    pending_posts = BlogPost.query.filter(
        BlogPost.created_at <= now,
        BlogPost.email_sent == False
    ).limit(MAX_EMAILS).all()

    if not pending_posts:
        return

    current_app.logger.info(f"📧 Skickar mail för {len(pending_posts)} inlägg")

    for post in pending_posts:
        try:
            notify_subscribers(post)
            post.email_sent = True
            db.session.commit()  # ✅ Commit efter varje lyckat mail
        except Exception as e:
            current_app.logger.error(f"❌ Mail-fel för post {post.id}: {e}")
            db.session.rollback()
            # ✅ Fortsätt med nästa post istället för att krascha


def notify_subscribers(post):
    """
    ✅ OPTIMERAD: Batch-skickar mail med connection pooling
    """
    subscribers = User.query.join(User.roles).filter(Role.name == "subscriber").all()
    
    if not subscribers:
        return

    # ✅ Skicka i batch om möjligt (beroende på mail-server)
    with mail.connect() as conn:  # ✅ Återanvänd connection
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
                conn.send(msg)  # ✅ Använd samma connection
            except Exception as e:
                current_app.logger.warning(f"⚠️ Kunde inte skicka till {subscriber.email}: {e}")
                continue  # ✅ Fortsätt med nästa