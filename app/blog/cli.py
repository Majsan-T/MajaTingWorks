# app/blog/cli.py
import click
from flask.cli import with_appcontext
from app.blog.utils import check_and_send_blog_emails

@click.command("send-blog-mails")
@with_appcontext
def send_blog_mails():
    """Skicka e-post om nya blogginlägg (max 10 åt gången)."""
    try:
        check_and_send_blog_emails()
        click.echo("✅ Blog emails checked and sent")
    except Exception as e:
        click.echo(f"❌ Error: {e}")