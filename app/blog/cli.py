# app/blog/cli.py
import click
from flask.cli import with_appcontext
from app.blog.utils import check_and_send_blog_emails

@click.command("send-blog-mails")
@with_appcontext
def send_blog_mails():
    """Skickar e-postnotifieringar för nya blogginlägg."""
    check_and_send_blog_emails()
