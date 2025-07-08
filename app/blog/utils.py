from flask_mail import Message
from flask import current_app, url_for
from app.models import User
from app import mail  # Se till att mail-instansen är korrekt importerad

def notify_subscribers(post):
    subscribers = User.query.filter_by(role="subscriber").all()
    if not subscribers:
        return

    for subscriber in subscribers:
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
