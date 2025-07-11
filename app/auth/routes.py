# app/auth/routes.py
from flask_login import login_required, current_user, logout_user
from app.extensions import db
from flask import Blueprint, redirect, url_for, flash, render_template, request

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    if request.method == "POST":
        user = current_user
        logout_user()
        db.session.delete(user)
        db.session.commit()
        flash("Ditt konto har tagits bort permanent.", "info")
        return redirect(url_for("pages.index"))
    return render_template("auth/delete_account.html")
