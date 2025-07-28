# app/pages/pages.py
from datetime import datetime
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, Response, session
from flask_mail import Message
from flask_login import login_required, current_user
from app.extensions import mail, db
from app.forms import ContactForm
from app.forms.shared_forms import CvEditForm
from app.models import CVContent, BlogPost, PortfolioItem, Category, db, PageView, BlogCategory

from app.utils.helpers import log_info
from app.utils.views import increment_post_views, increment_page_view
import requests

pages_bp = Blueprint("pages", __name__)


def verify_captchafox(response_token):
    secret = current_app.config["CAPTCHAFOX_SECRET_KEY"]
    resp = requests.post(
        "https://api.captchafox.com/siteverify",
        data={"secret": secret, "response": response_token},
        timeout=5
    )
    try:
        data = resp.json()
    except ValueError:
        print("⚠️ CAPTCHAFOX svarade inte med JSON or unreachable:", resp.text)
        return False
    return data.get("success", False)


@pages_bp.route('/')
def home():
    log_info("🛠 Adminpanelen laddades")
    year = datetime.now().year
    increment_post_views("home")
    return render_template('index.html', year=year)

@pages_bp.route("/about")
def about():
    increment_post_views("about")
    log_info("🛠 Adminpanelen laddades")
    return render_template("pages/about.html")

@pages_bp.route("/contact", methods=["GET", "POST"])
def contact():
    increment_post_views("contact")
    current_app.logger.info(f"Route /admin/ kördes av {current_user.email}")
    form = ContactForm()
    site_key = current_app.config.get("CAPTCHAFOX_SITE_KEY")

    if form.validate_on_submit():
        if not verify_captchafox(form.captcha_token.data):
            flash("Verifiering misslyckades. Försök igen.", "danger")
            return redirect(url_for("pages.contact"))

        try:
            msg = Message(
                subject=f"Meddelande från {form.name.data}",
                sender=form.email.data,
                recipients=["majathedeveloper@gmail.com"],
                body=form.message.data
            )
            mail.send(msg)
            flash("Tack för ditt meddelande!", "success")
        except Exception:
            flash("Det gick inte att skicka meddelandet. Försök igen.", "danger")
        return redirect(url_for("pages.contact"))

    elif form.is_submitted() and not form.validate():
        flash("Var vänlig fyll i alla fält korrekt.", "warning")

    return render_template("pages/contact.html", form=form, captcha_sitekey=site_key)


@pages_bp.route("/cv", methods=["GET", "POST"])
def cv():
    current_app.logger.info(f"Route /admin/ kördes av {current_user.email}")
    form = CvEditForm()
    increment_post_views("cv")

    # Se till att det alltid finns ett CVContent-objekt
    content = CVContent.query.first()
    if not content:
        content = CVContent()
        db.session.add(content)
        db.session.commit()

    # Hantera formulärinlämning
    if form.validate_on_submit() and current_user.is_authenticated and current_user.has_role("admin"):
        print("User authenticated:", current_user.is_authenticated)
        print("User role:", getattr(current_user, 'role', None))
        if form.validate_on_submit():
            print("Form validated successfully.")
        else:
            print("Form validation failed.")
        print("Saving to database...")
        print("about:", form.about.data)
        print("experience:", form.experience.data)
        print("education:", form.education.data)
        print("awards:", form.awards.data)
        print("skills:", form.skills.data)
        print("interests:", form.interests.data)
        content.about = form.about.data
        content.experience = form.experience.data
        content.education = form.education.data
        content.awards = form.awards.data
        content.skills = form.skills.data
        content.interests = form.interests.data
        db.session.commit()
        flash("CV uppdaterat!", "success")
        return redirect(url_for("pages.cv"))

    # Fyll i formuläret vid GET (för admin)
    if request.method == "GET" and current_user.is_authenticated and current_user.has_role("admin"):
        form.about.data = content.about
        form.experience.data = content.experience
        form.education.data = content.education
        form.awards.data = content.awards
        form.skills.data = content.skills
        form.interests.data = content.interests

    # Skicka alltid med content till mallen
    return render_template("pages/cv.html", form=form, content={
        "about": content.about or "",
        "experience": content.experience or "",
        "education": content.education or "",
        "awards": content.awards or "",
        "skills": content.skills or "",
        "interests": content.interests or "",
    })


@pages_bp.route("/sitemap.xml")
def sitemap():
    increment_page_view()
    pages = []
    today = datetime.utcnow().date().isoformat()

    # Statiska sidor
    static_routes = [
        ("pages.home", {}),
        ("pages.about", {}),
        ("pages.contact", {}),
        ("pages.cv", {}),
        ("portfolio.index", {}),
        ("blog.index", {})
    ]
    for endpoint, values in static_routes:
        pages.append({
            "loc": url_for(endpoint, _external=True, **values),
            "lastmod": today
        })

    # Blogginlägg
    blog_posts = BlogPost.query.all()
    for post in blog_posts:
        lastmod = post.updated_at.date().isoformat() if post.updated_at else post.created_at.date().isoformat()
        pages.append({
            "loc": url_for("blog.show_post", post_id=post.id, _external=True),
            "lastmod": lastmod
        })

    # Bloggkategorier
    blog_categories = BlogCategory.query.all()
    for cat in blog_categories:
        pages.append({
            "loc": url_for("blog.posts_by_category", category=cat.name, _external=True),
            "lastmod": today
        })

    # Portfolio
    portfolio_items = PortfolioItem.query.all()
    for item in portfolio_items:
        pages.append({
            "loc": url_for("portfolio.item", item_id=item.id, _external=True),
            "lastmod": item.date.date().isoformat()
        })

    # Portfoliokategorier
    portfolio_categories = Category.query.all()
    for cat in portfolio_categories:
        pages.append({
            "loc": url_for("portfolio.category_view", category=cat.name, _external=True),
            "lastmod": today
        })

    sitemap_xml = render_sitemap(pages)
    return Response(sitemap_xml, mimetype="application/xml")


def render_sitemap(pages):
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for page in pages:
        xml.append("  <url>")
        xml.append(f"    <loc>{page['loc']}</loc>")
        xml.append(f"    <lastmod>{page['lastmod']}</lastmod>")
        xml.append("  </url>")
    xml.append("</urlset>")
    return "\n".join(xml)
