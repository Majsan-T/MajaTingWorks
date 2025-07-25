# app/blog/utils.py
from flask_mail import Message
from flask import current_app, url_for
from app.models import User, BlogPost, db
from app.extensions import mail
from datetime import datetime, timezone

def check_and_send_blog_emails():
    now = datetime.now(timezone.utc)
    MAX_EMAILS = 10
    pending_posts = BlogPost.query.filter(
        BlogPost.created_at <= now,
        BlogPost.email_sent == False
    ).limit(MAX_EMAILS).all()

    current_app.logger.info(f"Hittade {len(pending_posts)} inlägg att skicka ut.")

    for post in pending_posts:
        try:
            notify_subscribers(post)
            post.email_sent = True
            db.session.commit()  # Kommitta varje lyckad enskilt
        except Exception as e:
            current_app.logger.error(f"❌ Misslyckades skicka mail för post {post.id}: {e}")
            db.session.rollback()


def notify_subscribers(post):
    from app.extensions import mail  # För att undvika cirkulär import

    subscribers = User.query.filter_by(role="subscriber").all()
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
            current_app.logger.warning(f"Kunde inte skicka mail till {subscriber.email}: {e}")
