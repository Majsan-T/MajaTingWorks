# app/blog/utils.py
from flask_mail import Message
from flask import current_app, url_for
from app.models import User, BlogPost, db
from app.extensions import mail
from datetime import datetime, timezone

def check_and_send_blog_emails():
    now = datetime.now(timezone.utc)
    pending_posts = BlogPost.query.filter(
        BlogPost.created_at <= now,
        BlogPost.email_sent == False
    ).all()

    for post in pending_posts:
        notify_subscribers(post)
        post.email_sent = True
    db.session.commit()  # Gör en enda commit efter loopen

def notify_subscribers(post):
    from app.extensions import mail  # ← Importera här för att undvika cirkulär import

    subscribers = User.query.filter_by(role="subscriber").all()
    if not subscribers:
        return

    for subscriber in subscribers:
        msg = Message(
            subject=f"Nytt blogginlägg: {post.title}",
            sender=current_app.config["MAIL_DEFAULT_SENDER"],
            recipients=[subscriber.email]
        )
        msg.body = f"""..."""
        mail.send(msg)

    post.email_sent = True
    db.session.commit()
