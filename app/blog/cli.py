# app/blog/cli.py
import click
from flask.cli import with_appcontext
from app.blog.utils import check_and_send_blog_emails

# ===================================================
# ✅ CLI-KOMMANDON FÖR BLOGGEN
# ===================================================

@click.command("send-blog-mails")
@with_appcontext
def send_blog_mails():
    """
    Skickar e-postnotifieringar för nya blogginlägg.

    ✅ Används via CLI (kommandoraden):
        flask send-blog-mails

    ✅ Funktion:
        - Hämtar blogginlägg som ännu inte skickats ut via e-post
        - Använder check_and_send_blog_emails() i blog.utils
        - Max 10 mail skickas åt gången (se utils-filen)
    """
    check_and_send_blog_emails()
