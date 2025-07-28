# app/portfolio/portfolio.py
# ================================================
# ✅ IMPORTER & KONFIGURATION
# ================================================
import os
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, current_app, abort
)
from flask_login import login_required, current_user
from app import db
from app.decorators import roles_required
from app.models import PortfolioItem, Category
from app.forms import PortfolioForm, DeleteForm
from app.utils.views import increment_post_views
from app.utils.image_utils import save_image, delete_existing_image, _handle_quill_upload
from app.utils.time import get_local_now
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import or_
from app.extensions import csrf

# Skapa Blueprint för portfolio
portfolio_bp = Blueprint('portfolio', __name__, template_folder='../../templates/portfolio')

# Standard antal poster per sida (paginering)
POSTS_PER_PAGE = 12


# ================================================
# ✅ INDEX – LISTA ALLA PORTFOLIO-PROJEKT
# ================================================
@portfolio_bp.route("/portfolio")
def index(page=1):
    """
    Visa en lista med alla portfolio-projekt:
    - Stöd för sortering (asc/desc)
    - Fritextsökning i titel och beskrivning
    - Filtrering på kategori
    - Paginering
    """
    increment_post_views("portfolio")
    PER_PAGE = 8

    # --- Hämta filter & sökparametrar ---
    sort_order     = request.args.get('sort',   'desc')
    search         = request.args.get('search', '').strip()
    category_id    = request.args.get('category_id', type=int)

    # --- Hämta kategorilista för filtermeny ---
    category_list = Category.query.order_by(Category.title).all()

    # --- Basquery ---
    q = PortfolioItem.query

    # --- Fritextsökning (dela upp ord för bättre träffar) ---
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

    # --- Filtrering på kategori ---
    if category_id:
        q = q.filter(PortfolioItem.category_id == category_id)

    # --- Sortering ---
    if sort_order == 'asc':
        q = q.order_by(PortfolioItem.date.asc())
    else:
        q = q.order_by(PortfolioItem.date.desc())

    # --- Paginering ---
    total = q.count()
    posts = q.offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()
    total_pages = (total + PER_PAGE - 1) // PER_PAGE

    # --- Senaste projekt för sidokolumnen ---
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

# ================================================
# ✅ VISA EN ENDAST PORTFOLIO-PROJEKT
# ================================================
@portfolio_bp.route("/portfolio/<int:item_id>")
def show_portfolio_item(item_id):
    """
    Visa ett enskilt portfolio-projekt:
    - Räknar visningar
    - Laddar föregående och nästa projekt
    - Paginering av övriga projekt (högerkolumn)
    """
    item = PortfolioItem.query.get_or_404(item_id)

    # ✅ Räkna visningar
    increment_post_views(f"portfolio_{item_id}")

    # ✅ Senaste projekt för högerkolumnen
    recent_posts = (
        PortfolioItem.query
        .order_by(PortfolioItem.date.desc())
        .limit(5)
        .all()
    )

    # ✅ Föregående och nästa baserat på datum
    prev_item = (
        PortfolioItem.query
        .filter(PortfolioItem.date < item.date)
        .order_by(PortfolioItem.date.desc())
        .first()
    )
    next_item = (
        PortfolioItem.query
        .filter(PortfolioItem.date > item.date)
        .order_by(PortfolioItem.date.asc())
        .first()
    )

    # ✅ Högerkolumn: Paginering (visa 10 st)
    page = request.args.get("page", 1, type=int)
    PER_PAGE = 10
    total_posts = PortfolioItem.query.count()
    total_pages = (total_posts + PER_PAGE - 1) // PER_PAGE

    posts = (
        PortfolioItem.query
        .order_by(PortfolioItem.date.desc())
        .offset((page - 1) * PER_PAGE)
        .limit(PER_PAGE)
        .all()
    )

    return render_template(
        "portfolio/portfolio_item.html",
        item=item,
        prev_item=prev_item,
        next_item=next_item,
        posts=posts,
        page=page,
        total_pages=total_pages
    )

# ================================================
# ✅ SKAPA NYTT PORTFOLIO-PROJEKT
# ================================================
@portfolio_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def create_portfolio():
    """
    Skapa ett nytt portfolio-projekt:
    - Kräver admin-behörighet
    - Laddar kategori-val
    - Sparar ev. uppladdad bild som .webp
    """
    form = PortfolioForm()

    if form.validate_on_submit():
        print("\U0001f4be Spara portfolio-bild")
        filename = None
        if form.image.data:
            # ✅ Bild sparas som .webp i uploads/portfolio och returnerar nytt filnamn
            filename = save_image(form.image.data, folder="uploads/portfolio")

        new_item = PortfolioItem(
            title=form.title.data,
            description=form.description.data,
            image=filename,
            category_id=form.category.data,
            date=get_local_now()  # ✅ Sätt aktuell tid i rätt tidszon
        )

        db.session.add(new_item)
        db.session.commit()
        flash("Portfolio-inlägget har skapats!", "success")
        return redirect(url_for('portfolio.index'))

    return render_template('portfolio/new_portfolio_item.html', form=form)

# ================================================
# ✅ REDIGERA PORTFOLIO-PROJEKT
# ================================================
@portfolio_bp.route('/portfolio/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
@roles_required("admin")
def edit_portfolio(item_id):
    """
    Redigera ett befintligt portfolio-projekt:
    - Kräver admin
    - Stöd för att behålla, byta eller ta bort bild
    """
    increment_post_views(f"portfolio_{item_id}")
    item = PortfolioItem.query.get_or_404(item_id)
    form = PortfolioForm(obj=item)

    if form.validate_on_submit():
        try:
            # ✅ Uppdatera text & metadata
            item.title = form.title.data
            item.description = form.description.data
            item.category_id = form.category.data

            # ✅ Hantera bild (behåll, ta bort eller byt)
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

            # ✅ Spara i databasen
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

# ================================================
# ✅ RADERA PORTFOLIO-PROJEKT
# ================================================
@portfolio_bp.route('/portfolio/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_portfolio(item_id):
    """
    Radera ett portfolio-projekt:
    - Kräver admin
    - Raderar även kopplad bild (om finns)
    """
    item = PortfolioItem.query.get_or_404(item_id)

    if not current_user.has_role("admin"):
        flash("Endast administratörer kan ta bort inlägg.", "danger")
        return redirect(url_for('portfolio.item', item_id=item.id))

    # ✅ Radera posten (och ev. bild)
    if item.image:
        try:
            delete_existing_image(item.image, folder="uploads/portfolio")
        except Exception as e:
            current_app.logger.warning(f"⚠️ Kunde inte radera bild {item.image}: {e}")


    db.session.delete(item)
    db.session.commit()
    flash("Inlägget har tagits bort.", "success")
    return redirect(url_for('portfolio.index'))

# ================================================
# ✅ VISA ENSKILT PROJEKT (inkl. relaterade projekt)
# ================================================
@portfolio_bp.route('/portfolio/<int:item_id>')
def item(item_id):
    """
    Visa ett enskilt portfolio-projekt:
    - Paginering av senaste projekt i högerkolumnen
    - Visar även "relaterade" (senaste) projekt
    """
    increment_post_views(f"portfolio_{item_id}")  # ✅ Räkna visningar
    item = PortfolioItem.query.get_or_404(item_id)

    # ✅ Paginera senaste projekt (högerkolumn)
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

# ================================================
# ✅ DEBUG-VY (visar rå beskrivning)
# ================================================
@portfolio_bp.route("/debug/<int:item_id>")
def debug_item(item_id):
    """
    Endast för felsökning:
    - Skriver ut rå beskrivning i <pre>-format
    """
    item = PortfolioItem.query.get_or_404(item_id)
    return f"<pre>{item.description}</pre>"


# ================================================
# ✅ VISA PROJEKT PER KATEGORI
# ================================================
@portfolio_bp.route("/portfolio/category/<string:category>")
@portfolio_bp.route("/portfolio/category/<string:category>/page/<int:page>")
def category_view(category, page=1):
    """
    Visa portfolio-projekt baserat på kategori:
    - Paginering
    - Fritextsökning & sortering
    """
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

# ================================================
# ✅ RADERA KATEGORI (endast admin)
# ================================================
@portfolio_bp.route("/portfolio/delete-category/<int:category_id>", methods=["POST"])
@login_required
@roles_required("admin")
def delete_category(category_id):
    """
    Radera en kategori:
    - Kan endast raderas om den inte innehåller projekt
    """
    category = Category.query.get_or_404(category_id)
    if category.items:
        flash("Kan inte radera kategori som innehåller projekt.", "danger")
    else:
        db.session.delete(category)
        db.session.commit()
        flash("Kategorin har raderats.", "success")
    return redirect(url_for("admin.manage_portfolio_categories"))

# ================================================
# ✅ ADMIN – HANTERA PORTFOLIO-ITEMS
# ================================================
@portfolio_bp.route("/portfolio/manage-items")
@login_required
@roles_required("admin")
def manage_items():
    """
    Adminvy för att hantera portfolio-projekt:
    - Paginering & sortering
    """
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

# ================================================
# ✅ UPPLADDNING AV BILDER (Quill-editor)
# ================================================
@portfolio_bp.route('/upload', methods=['POST'])
@login_required
@roles_required("admin")
@csrf.exempt
def upload_portfolio_image():
    """
    Uppladdning av bilder via Quill-editorn:
    - Konverterar till .webp
    - Lagrar i uploads/portfolio
    """
    return _handle_quill_upload(folder="uploads/portfolio")