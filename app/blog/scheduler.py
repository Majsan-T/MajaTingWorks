from datetime import datetime, timezone
from app.models import BlogPost, db
from app.blog.utils import notify_subscribers

def check_and_notify_posts():
    now = datetime.now(timezone.utc)
    posts_to_notify = BlogPost.query.filter(
        BlogPost.created_at <= now,
        BlogPost.notified == False
    ).all()

    for post in posts_to_notify:
        notify_subscribers(post)
        post.notified = True
        db.session.commit()
