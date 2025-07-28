import datetime
import bleach
import pytz
from bs4 import BeautifulSoup
from datetime import datetime, date, time
from flask import current_app, request
from flask_login import current_user
from markupsafe import Markup, escape 

# Standardtidszon för hela appen
DEFAULT_TZ = pytz.timezone("Europe/Stockholm")

def get_local_now():
    """
    ✅ Returnerar aktuell tid i Europe/Stockholm-tidszon.
    - Används vid sparande av inlägg, kommentarer m.m.
    """
    return datetime.now(DEFAULT_TZ)


def strip_and_truncate(html, length=100):
    """
    ✅ Tar bort HTML-taggar och trunkerar texten.
    - Används t.ex. för korta utdrag i listor.
    """
    if not html:
        return ""
    text = BeautifulSoup(html, "html.parser").get_text()
    return text[:length] + ("..." if len(text) > length else "")


def pluralize(word, count):
    """
    ✅ En enkel pluralfunktion för svenska.
    - Lägger till "er" om count != 1.
    """
    return word if count == 1 else word + "er"


def safe_filename(name):
    """
    ✅ Rensar filnamn från ogiltiga tecken.
    - Ersätter med understreck (_).
    - Används innan fil sparas på servern.
    """
    import re
    return re.sub(r'[^\w\-_\. ]', '_', name).strip()


def linebreaks(text, allow_html=False):
    """
    ✅ Konverterar radbrytningar (\n) till <br>.
    - Om allow_html=True: tillåt vissa HTML-taggar men rensa annat med bleach.
    - Annars: escapear allt och ersätter bara med <br>.
    """
    if not text:
        return ""
    if allow_html:
        allowed_tags = ['p', 'br', 'ul', 'ol', 'li', 'b', 'i', 'strong', 'em', 'a']
        allowed_attrs = {
            'a': ['href', 'title', 'rel']
        }
        cleaned = bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs, strip=True)
        return Markup(cleaned.replace('\n', '<br>'))
    safe_text = escape(text)
    return Markup(safe_text.replace('\n', '<br>'))


def sanitize_html(html):
    """
    ✅ Rensar HTML (t.ex. från Quill-editor) men tillåter vissa formateringar.
    - Tar bort farliga taggar och attribut.
    - Används vid sparande av blogg- och portfolioinlägg.
    """
    allowed_tags = [
        'p', 'strong', 'em', 'u', 'ul', 'ol', 'li', 'br', 'i',
        'a', 'blockquote', 'code', 'pre', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
    ]
    allowed_attrs = {
        '*': ['class'],
        'a': ['href', 'title', 'target'],
        'img': ['src', 'alt']
    }
    return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)


def log_info(message: str):
    """
    ✅ Loggar en informationsrad i serverns logg.
    - Lägger till inloggad användares e-post (eller 'Anonymous').
    - Lägger även till IP-adressen.
    - Används t.ex. i adminpanelen vid känsliga åtgärder.
    """
    user_email = current_user.email if current_user.is_authenticated else "Anonymous"
    ip_address = request.remote_addr or "Unknown IP"
    current_app.logger.info(f"{message} (User: {user_email}, IP: {ip_address})")
