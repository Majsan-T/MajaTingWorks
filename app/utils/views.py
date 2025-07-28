# app/utils/views.py
from flask import request, session
from app.models import db, PageView

def increment_post_views(target):
    """
    ✅ Räknar visningar (unika per session):
    - Om `target` är ett BlogPost-objekt → Räknar visningar baserat på postens ID.
    - Om `target` är en sträng → Räknar visningar på sidnivå (t.ex. 'about', 'portfolio_12').
    - Räknar endast en gång per session och sparar i `session["viewed_posts"]`.

    Returnerar det uppdaterade antalet visningar (int).
    """
    if "viewed_posts" not in session:
        session["viewed_posts"] = []

    # ✅ Bloggpost (target = BlogPost-objekt)
    if hasattr(target, "id"):
        post_id = f"post_{target.id}"
        if post_id not in session["viewed_posts"]:
            target.views = (target.views or 0) + 1
            db.session.commit()
            session["viewed_posts"].append(post_id)
        return target.views

    # ✅ Vanliga sidor & portfolio (target = sträng)
    elif isinstance(target, str):
        page = PageView.query.filter_by(page=target).first()
        if not page:
            page = PageView(page=target, views=1)
            db.session.add(page)
        else:
            page.views += 1
        db.session.commit()
        return page.views

    return 0

def increment_page_view(page_name: str = None):
    """
    ✅ Räknar unika sidvisningar (unika per session):
    - Tar emot sidans namn (`page_name`) eller hämtar från request.endpoint.
    - Sparar unika visningar i `session["viewed_pages"]`.
    - Returnerar det uppdaterade antalet visningar (int).
    """
    if "viewed_pages" not in session:
        session["viewed_pages"] = []

    if not page_name:
        page_name = request.endpoint.split(".")[-1]  # Exempel: 'about', 'cv'

    if page_name not in session["viewed_pages"]:
        page = PageView.query.filter_by(page=page_name).first()

        if not page:
            page = PageView(page=page_name, views=1)
            db.session.add(page)
        else:
            page.views += 1

        db.session.commit()
        session["viewed_pages"].append(page_name)

    page = PageView.query.filter_by(page=page_name).first()
    return page.views if page else 0
