# app/auth/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from datetime import datetime, timezone
from itsdangerous import URLSafeTimedSerializer as Serializer, SignatureExpired, BadSignature

from app.extensions import db, login_manager, mail
from app.models import User, Comment, BlogPost
from app.forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm, DeleteForm
from app.forms.auth_forms import SetPasswordForm

auth_bp = Blueprint("auth", __name__)


# ======================
# ✅ TOKEN-UTILITIES
# ======================

def generate_token(email):
    """Generera en tidsbegränsad token för lösenordsåterställning."""
    s = Serializer(current_app.config["SECRET_KEY"], salt="password-reset")
    return s.dumps({"email": email})


def verify_token(token, expiration=3600):
    """Verifiera token och returnera e-postadressen om giltig."""
    s = Serializer(current_app.config["SECRET_KEY"], salt="password-reset")
    try:
        data = s.loads(token, max_age=expiration)
    except Exception:
        return None
    return data.get("email")


@login_manager.user_loader
def load_user(user_id):
    """Ladda en användare baserat på användar-ID (för Flask-Login)."""
    return User.query.get(int(user_id))


# ======================
# ✅ AUTHENTICATION ROUTES
# ======================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Registrera en ny användare."""
    form = RegisterForm()
    form.set_role_choices()  # ✅ Visa endast roller som är tillåtna vid registrering (ej admin)

    if form.validate_on_submit():
        # ⚠️ Kontrollera om e-post redan finns
        if User.query.filter_by(email=form.email.data).first():
            flash("En användare med den e-posten finns redan.", "warning")
            return redirect(url_for("auth.register"))

        # ✅ Skapa användaren
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8)
        )

        # ✅ Tilldela roller (standard: user)
        if form.roles.data:
            for role_name in form.roles.data:
                new_user.add_role(role_name)
        else:
            new_user.add_role("user")

        db.session.add(new_user)
        db.session.commit()

        # ✅ Logga in användaren direkt efter registrering
        login_user(new_user)
        flash("✅ Ditt konto har skapats!", "success")
        return redirect(url_for("pages.home"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Logga in en användare."""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if not user or not check_password_hash(user.password, form.password.data):
            flash("Det gick inte att logga in. Kontrollera email och lösenord.")
            return redirect(url_for("auth.login"))

        current_app.logger.info(f"✅ Login lyckades för {user.email}")
        login_user(user)
        return redirect(url_for("blog.index"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
def logout():
    """Logga ut den aktuella användaren."""
    logout_user()
    return redirect(url_for("blog.index"))


# ======================
# ✅ ACCOUNT MANAGEMENT
# ======================

@auth_bp.route("/account", methods=["GET"])
@login_required
def account():
    """Visa kontoöversikt för den inloggade användaren."""
    page = request.args.get("page", 1, type=int)
    comments = Comment.query.filter_by(author_id=current_user.id) \
        .order_by(Comment.date_created.desc()) \
        .paginate(page=page, per_page=5)

    delete_form = DeleteForm()
    cookies = request.cookies  # ✅ Hämta cookies dynamiskt

    return render_template(
        "auth/account.html",
        user=current_user,
        comments=comments,
        delete_form=delete_form,
        cookies=cookies
    )


@auth_bp.route("/deactivate_account", methods=["POST"])
@login_required
def deactivate_account():
    """Inaktivera och anonymisera kontot (GDPR)."""
    user = current_user
    user.anonymize()  # ✅ Använder din befintliga anonymiseringsmetod
    db.session.commit()

    logout_user()
    flash("Ditt konto har inaktiverats och anonymiserats enligt GDPR.", "info")
    return redirect(url_for("pages.home"))


@auth_bp.route("/delete_account", methods=["POST"])
@login_required
def delete_account():
    """Radera kontot permanent (GDPR)."""
    user = current_user

    # ✅ Ta bort kommentarer och användare
    Comment.query.filter_by(author_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()

    logout_user()
    flash("Ditt konto och all data har raderats permanent.", "danger")
    return redirect(url_for("pages.home"))


@auth_bp.route("/reactivate_account", methods=["POST"])
@login_required
def reactivate_account():
    """Återaktivera ett tidigare inaktiverat konto."""
    user = current_user

    if not user.is_deleted and user._is_active:
        flash("✅ Ditt konto är redan aktivt.", "info")
        return redirect(url_for("auth.account"))

    user.is_deleted = False
    user._is_active = True
    user.deleted_at = None
    db.session.commit()

    flash("✅ Ditt konto har återaktiverats och är nu aktivt igen.", "success")
    return redirect(url_for("auth.account"))


# ======================
# ✅ PASSWORD RESET
# ======================

@auth_bp.route("/request-reset", methods=["GET", "POST"])
def request_reset():
    """Begär återställningslänk via e-post."""
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = generate_token(user.email)
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            msg = Message(
                subject="Återställ ditt lösenord",
                recipients=[user.email]
            )
            msg.body = f"""Hej {user.name},

Klicka på länken för att återställa ditt lösenord:
{reset_url}

Länken går ut om 1 timme."""
            mail.send(msg)
            flash("En återställningslänk har skickats till din e-post.", "info")
        else:
            flash("Ingen användare med den e-postadressen.", "warning")
        return redirect(url_for("auth.login"))
    return render_template("auth/request_reset.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Återställ lösenord med hjälp av token."""
    email = verify_token(token)
    if not email:
        flash("Länken är ogiltig eller har gått ut.", "danger")
        return redirect(url_for("auth.request_reset"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash("Ditt lösenord är återställt. Du kan nu logga in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)


@auth_bp.route('/set-password/<token>', methods=['GET', 'POST'])
def set_password(token):
    """Sätt lösenord (för användare skapade av admin)."""
    form = SetPasswordForm()
    serializer = Serializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except (SignatureExpired, BadSignature):
        flash("Länken är ogiltig eller har gått ut.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first_or_404()
    if form.validate_on_submit():
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash("Lösenordet är satt. Du kan nu logga in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/set_password.html", form=form)


# ======================
# ✅ COMMENTS
# ======================

@auth_bp.route("/delete-comment/<int:comment_id>", methods=["POST"])
@login_required
def delete_comment(comment_id):
    """Ta bort en kommentar (endast egna kommentarer)."""
    comment = Comment.query.get_or_404(comment_id)
    if comment.author_id != current_user.id:
        flash("Du kan bara ta bort dina egna kommentarer.", "danger")
        return redirect(url_for("auth.account"))

    db.session.delete(comment)
    db.session.commit()
    flash("Kommentaren har tagits bort.", "success")
    return redirect(url_for("auth.account"))
