# app/auth/auth.py
from itsdangerous import URLSafeTimedSerializer as Serializer, SignatureExpired, BadSignature
from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_user, logout_user, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager, mail
from app.forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm
from app.forms.auth_forms import SetPasswordForm
from app.models import User

auth_bp = Blueprint("auth", __name__)

def generate_token(email):
    s = Serializer(current_app.config["SECRET_KEY"], salt="password-reset")
    return s.dumps({"email": email})

def verify_token(token, expiration=3600):
    s = Serializer(current_app.config["SECRET_KEY"], salt="password-reset")
    try:
        data = s.loads(token, max_age=expiration)
    except Exception:
        return None
    return data.get("email")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        selected_role = form.role.data # Detta kommer nu alltid vara "user" om det är det enda valet i formuläret

        # Denna if-sats blir i princip redundant, men den skadar inte
        # if selected_role == "admin" and (not current_user.is_authenticated or current_user.role != "admin"):
        #     selected_role = "user" # Eller bara sätt selected_role = "user" här direkt om du vill vara säker

        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8),
            role=selected_role
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('pages.home'))
    return render_template("auth/register.html", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user or not check_password_hash(user.password, form.password.data):
            flash("Det gick inte att logga in. Kontrollera email och lösenord.")
            return redirect(url_for("auth.login"))
        login_user(user)
        return redirect(url_for("blog.index"))
    return render_template("auth/login.html", form=form)

@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("blog.index"))

@auth_bp.route("/request-reset", methods=["GET", "POST"])
def request_reset():
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = generate_token(user.email)
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            # Skicka e-post här – exempel med print:
            msg = Message(
                subject="Återställ ditt lösenord",
                recipients=[user.email]
            )
            msg.body = f"""
            Hej {user.email},

            Du har begärt att få återställa ditt lösenord. Klicka på länken nedan för att ange ett nytt:

            {reset_url}

            Länken går ut om 1 timme. Om du inte begärde detta kan du bortse från mejlet.

            Vänliga hälsningar,
            Ditt Team
            """
            mail.send(msg)

            flash("En återställningslänk har skickats till din e-post.", "info")
        else:
            flash("Finns ingen användare med den e-postadressen.", "warning")
        return redirect(url_for("auth.login"))
    return render_template("auth/request_reset.html", form=form)

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
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
    form = SetPasswordForm()
    serializer = Serializer(current_app.config['SECRET_KEY'])

    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash("❌ Länken har gått ut. Be administratören om en ny.", "danger")
        return redirect(url_for("auth.login"))
    except BadSignature:
        flash("❌ Ogiltig länk. Den kan ha blivit skadad eller använd tidigare.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first_or_404()

    if form.validate_on_submit():
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash("✅ Lösenordet är satt. Du kan nu logga in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/set_password.html", form=form)