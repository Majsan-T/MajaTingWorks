# app/utils/helpers.py
import datetime
import bleach
import pytz
from bs4 import BeautifulSoup
from datetime import datetime, date, time
from flask import current_app
from markupsafe import Markup, escape 

DEFAULT_TZ = pytz.timezone("Europe/Stockholm")

def get_local_now():
    """Returnerar aktuell tid med Stockholm-tidszon."""
    return datetime.now(DEFAULT_TZ)

# Din befintliga strip_and_truncate (behåll om den används)
def strip_and_truncate(html, length=100):
    if not html:
        return ""
    text = BeautifulSoup(html, "html.parser").get_text()
    return text[:length] + ("..." if len(text) > length else "")

# Din befintliga pluralize (behåll om den används)
def pluralize(word, count):
    return word if count == 1 else word + "er"

# Din befintliga safe_filename (behåll om den används)
def safe_filename(name):
    import re
    return re.sub(r'[^\w\-_\. ]', '_', name).strip()

# Din befintliga linebreaks (behåll om den används)
def linebreaks(text, allow_html=False):
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

# Din sanitize_html för att rensa HTML från Quill
def sanitize_html(html):
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

# Om notify_subscribers() FUNGERAR OCH FINNS någonstans,
# PLACERA DEN HÄR. Om den inte finns eller inte fungerar, ta bort den.
# Exempel (du måste fylla i detaljer):
# def notify_subscribers(blog_post):
#     # Logik för att skicka e-post, push-notiser etc.
#     print(f"Noterar prenumeranter om nytt inlägg: {blog_post.title}")
#     pass