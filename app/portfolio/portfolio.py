# app/portfolio/portfolio.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, redirect, abort
from flask_login import login_required, current_user
from app import db
from app.decorators import admin_only
from app.models import PortfolioItem, Category
from app.forms import PortfolioForm, DeleteForm
from app.utils.image_utils import save_image, delete_existing_image, _handle_quill_upload
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from sqlalchemy import or_, and_
from app.utils.time import get_local_now
import sys
from app.extensions import csrf


portfolio_bp = Blueprint('portfolio', __name__, template_folder='../../templates/portfolio')
POSTS_PER_PAGE = 12

@portfolio_bp.route("/portfolio")
@portfolio_bp.route("/portfolio/page/<int:page>")
def index(page=1):
    PER_PAGE = 8
    sort_order     = request.args.get('sort',   'desc')
    search         = request.args.get('search', '').strip()
    # Byt till category_id – så det matchar ditt template
    category_id    = request.args.get('category_id', type=int)

    # 1) Hämta alla kategorier
    category_list = Category.query.order_by(Category.title).all()

    # 2) Bas‐query
    q = PortfolioItem.query
    # 3) Fritextsökning på title + description
    if search:
        # Dela upp på mellanslag så att alla ord måste matcha
        words = search.split()
        for w in words:
            pattern = f"%{w}%"
            q = q.filter(
                or_(
                    PortfolioItem.title.ilike(pattern),
                    PortfolioItem.description.ilike(pattern)
                )
            )
    # 4) Kategorifilter
    if category_id:
        q = q.filter(PortfolioItem.category_id == category_id)

    # 5) Sortera
    if sort_order == 'asc':
        q = q.order_by(PortfolioItem.date.asc())
    else:
        q = q.order_by(PortfolioItem.date.desc())

    # 6) Paginerings-logik
    total = q.count()
    posts = q.offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()
    total_pages = (total + PER_PAGE - 1) // PER_PAGE

    # 7) Senaste projekt för höger kolumn
    recent_posts = (
        PortfolioItem.query
        .order_by(PortfolioItem.date.desc())
        .limit(8)
        .all()
    )

    return render_template(
        "portfolio/portfolio.html",
        category_list     = category_list,
        posts             = posts,
        recent_posts      = recent_posts,
        page              = page,
        total_pages       = total_pages,
        sort_order        = sort_order,
        search            = search,
        current_category  = category_id
    )

@portfolio_bp.route("/create", methods=["GET", "POST"])
@login_required
@admin_only
def create_portfolio():
    form = PortfolioForm()

    if form.validate_on_submit():
        print("\U0001f4be Spara portfolio-bild")
        filename = None
        if form.image.data:
            # Bild sparas som .webp i uploads/portfolio och returnerar nytt filnamn
            filename = save_image(form.image.data, folder="uploads/portfolio")

        new_item = PortfolioItem(
            title=form.title.data,
            description=form.description.data,
            image=filename,
            category_id=form.category.data,
            date=get_local_now()
        )

        db.session.add(new_item)
        db.session.commit()
        flash("Portfolio-inlägget har skapats!", "success")
        return redirect(url_for('portfolio.index'))

    return render_template('portfolio/new_portfolio_item.html', form=form)

@portfolio_bp.route('/portfolio/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
@admin_only
def edit_portfolio(item_id):
    item = PortfolioItem.query.get_or_404(item_id)
    form = PortfolioForm(obj=item)

    if form.validate_on_submit():
        try:
            item.title = form.title.data
            item.description = form.description.data
            item.category_id = form.category.data

            # ✅ Bildhantering
            action = form.image_action.data
            if action == "delete":
                if item.image:
                    delete_existing_image(item.image)
                item.image = None

            elif action == "replace" and form.image.data:
                # Spara ny bild som .webp och ta bort tidigare (om finns)
                new_filename = save_image(form.image.data, folder="uploads/portfolio")
                if item.image:
                    delete_existing_image(item.image, folder="uploads/portfolio")
                item.image = new_filename

            # action == "keep": inget ändras

            db.session.commit()
            flash("Inlägget har uppdaterats!", "success")
            return redirect(url_for('portfolio.item', item_id=item.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database commit failed for item ID: {item.id}. Error: {e}", exc_info=True)
            flash(f"Ett fel uppstod vid uppdatering: {e}", "danger")
    else:
        if request.method == 'POST':
            current_app.logger.warning("--- Form Submission Failed Validation ---")
            current_app.logger.debug(f"Request Form Data (on validation fail): {request.form}")
            current_app.logger.error(f"Form Errors: {form.errors}")

    return render_template("portfolio/edit_portfolio_item.html", form=form, item=item)

@portfolio_bp.route('/portfolio/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_portfolio(item_id):
    item = PortfolioItem.query.get_or_404(item_id)

    if current_user.role != 'admin':
        flash("Endast administratörer kan ta bort inlägg.", "danger")
        return redirect(url_for('portfolio.item', item_id=item.id))

    db.session.delete(item)
    db.session.commit()
    flash("Inlägget har tagits bort.", "success")
    return redirect(url_for('portfolio.index'))

@portfolio_bp.route('/portfolio/<int:item_id>')
def item(item_id):
    item = PortfolioItem.query.get_or_404(item_id)

    # Hämta paginerad lista med senaste projekt
    recent_page = request.args.get("recent_page", 1, type=int)
    per_page = 5
    recent_query = PortfolioItem.query.filter(PortfolioItem.id != item_id).order_by(PortfolioItem.date.desc())
    total = recent_query.count()
    recent_posts = recent_query.offset((recent_page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page
    delete_form = DeleteForm()

    return render_template(
        "portfolio/portfolio_item.html",
        item=item,
        recent_posts=recent_posts,
        recent_page=recent_page,
        recent_total_pages=total_pages,
        delete_form=delete_form
    )

@portfolio_bp.route("/debug/<int:item_id>")
def debug_item(item_id):
    item = PortfolioItem.query.get_or_404(item_id)
    return f"<pre>{item.description}</pre>"

@portfolio_bp.route("/portfolio/category/<string:category>")
@portfolio_bp.route("/portfolio/category/<string:category>/page/<int:page>")
def category_view(category, page=1):
    PER_PAGE = 12
    sort_order = request.args.get('sort', 'desc')
    search = request.args.get('search', '').strip()

    category_obj = Category.query.filter_by(name=category).first_or_404()

    query = PortfolioItem.query.filter_by(category_id=category_obj.id)
    if search:
        query = query.filter(PortfolioItem.title.ilike(f"%{search}%"))
    if sort_order == 'asc':
        query = query.order_by(PortfolioItem.date.asc())
    else:
        query = query.order_by(PortfolioItem.date.desc())

    total = query.count()
    posts = query.offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()
    total_pages = (total + PER_PAGE - 1) // PER_PAGE

    return render_template(
        "portfolio/portfolio_category_view.html",
        category=category_obj.name,
        category_title=category_obj.title,
        category_description=category_obj.description,
        posts=posts,
        page=page,
        total_pages=total_pages,
        sort_order=sort_order,
        search=search,
        current_category_obj=category_obj  # tillagt här
    )

@portfolio_bp.route("/portfolio/delete-category/<int:category_id>", methods=["POST"])
@login_required
@admin_only
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.items:
        flash("Kan inte radera kategori som innehåller projekt.", "danger")
    else:
        db.session.delete(category)
        db.session.commit()
        flash("Kategorin har raderats.", "success")
    return redirect(url_for("admin.manage_portfolio_categories"))

@portfolio_bp.route("/portfolio/manage-items")
@login_required
@admin_only
def manage_items():
    page = request.args.get("page", 1, type=int)
    if page < 1:
        abort(404)
    PER_PAGE = 12

    query = PortfolioItem.query.order_by(PortfolioItem.date.desc())
    total = query.count()
    posts = query.offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()
    total_pages = (total + PER_PAGE - 1) // PER_PAGE

    return render_template(
        "portfolio/manage_portfolio_items.html",
        posts=posts,
        page=page,
        total_pages=total_pages,
        delete_form=DeleteForm()
    )

@portfolio_bp.route('/upload', methods=['POST'])
@login_required
@admin_only
@csrf.exempt
def upload_portfolio_image():
    return _handle_quill_upload(folder="uploads/portfolio")