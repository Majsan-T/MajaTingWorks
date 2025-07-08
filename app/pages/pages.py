# app/pages/pages.py
from datetime import datetime
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app
from app.forms import ContactForm
from flask_mail import Message
from app.extensions import mail  # importera mail-objektet
from flask_login import login_required, current_user
from app.extensions import db
from app.models import CVContent
from app.forms.shared_forms import CvEditForm
from app.models import BlogPost  # Glöm inte importera modellen!
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
    year = datetime.now().year
    print(f"App root path: {current_app.root_path}")
    return render_template('index.html', year=year)

# Testsida
@pages_bp.route('/test')
def test():
    return render_template('test.html')


@pages_bp.route("/about")
def about():
    return render_template("pages/about.html")

@pages_bp.route("/contact", methods=["GET", "POST"])
def contact():
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
    form = CvEditForm()

    # Se till att det alltid finns ett CVContent-objekt
    content = CVContent.query.first()
    if not content:
        content = CVContent()
        db.session.add(content)
        db.session.commit()

    # Hantera formulärinlämning
    if form.validate_on_submit() and current_user.is_authenticated and current_user.role == "admin":
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
    if request.method == "GET" and current_user.is_authenticated and current_user.role == "admin":
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
