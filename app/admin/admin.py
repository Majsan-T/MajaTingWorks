# app/admin/admin.py
import os
import re
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, render_template, current_app, flash, request, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_mail import Message
from sqlalchemy import asc, desc
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from itsdangerous import URLSafeTimedSerializer
from PIL import Image

from app.decorators import roles_required
from app.extensions import db, mail
from app.utils.helpers import log_info
from app.blog.utils import check_and_send_blog_emails
from app.models import (
    User, BlogPost, Comment, BlogCategory, Category,
    PortfolioItem, PageView, Role
)
from app.forms.auth_forms import AdminCreateUserForm
from app.forms.blog_forms import BlogCategoryForm
from app.forms.shared_forms import (
    AdminUserForm, UserUpdateForm, CommentForm, DeleteForm,
    ImageDeleteForm, ApproveForm, EmptyForm
)
from app.forms.portfolio_forms import CategoryForm

# ======================
# ✅ ADMIN BLUEPRINT
# ======================
admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder="templates")


# ======================
# ✅ UTILITIES
# ======================

def generate_reset_token(email):
    """Skapa en tidsbegränsad token för återställning av lösenord."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')


# ======================
# ✅ ADMIN – DASHBOARD
# ======================
@admin_bp.route('/')
@login_required
@roles_required("admin")
def admin_dashboard():
    """Visa en översikt av användare, inlägg, kommentarer och statistik."""
    log_info("🛠 Adminpanelen laddades")
    user_count = User.query.count()
    post_count = BlogPost.query.count()
    comment_count = Comment.query.count()
    delete_form = DeleteForm()
    mail_form = EmptyForm()

    flagged_comments = Comment.query.filter_by(flagged=True).all()

    total_post_views = db.session.query(db.func.sum(BlogPost.views)).scalar() or 0
    total_page_views = db.session.query(db.func.sum(PageView.views)).scalar() or 0

    # Sektioner för dashboard-länkar
    dashboard_sections = [
        {
            "title": "Användaradministration",
            "links": [
                {"label": "Hantera användare", "endpoint": "admin.manage_users", "icon": "bi bi-person-fill-gear"},
                {"label": "Lägg till användare", "endpoint": "admin.create_user", "icon": "bi bi-person-fill-add"},
            ]
        },
        {
            "title": "Blogginlägg",
            "links": [
                {"label": "Hantera blogginlägg", "endpoint": "admin.manage_posts", "icon": "bi bi-journal"},
                {"label": "Skapa nytt blogginlägg", "endpoint": "blog.new_post", "icon": "bi bi-journal-plus"},
                {"label": "Hantera blogg-kategorier", "endpoint": "admin.manage_blog_categories", "icon": "bi bi-journal-bookmark"}
            ]
        },
        {
            "title": "Kommentarer",
            "links": [
                {"label": "Hantera kommentarer", "endpoint": "admin.manage_comments", "icon": "bi bi-chat-dots"}
            ]
        },
        {
            "title": "Portfolio",
            "links": [
                {"label": "Hantera portfolio-inlägg", "endpoint": "admin.manage_portfolio_item", "icon": "bi bi-folder-check"},
                {"label": "Lägg till portfolio-inlägg", "endpoint": "portfolio.create_portfolio", "icon": "bi bi-folder-plus"},
                {"label": "Hantera kategorier", "endpoint": "admin.manage_portfolio_categories", "icon": "bi bi-tags"}
            ]
        },
        {
            "title": "Bilder & Kategorier",
            "links": [
                {"label": "Hantera uppladdade bilder", "endpoint": "admin.manage_uploads", "icon": "bi bi-image"},
                {"label": "Rensa oanvända bilder", "endpoint": "admin.cleanup_unused_images", "icon": "bi bi-trash"},
            ]
        },
    ]

    return render_template(
        "admin/dashboard.html",
        user_count=user_count,
        post_count=post_count,
        comment_count=comment_count,
        flagged_comments=flagged_comments,
        dashboard_sections=dashboard_sections,
        delete_form = delete_form,
        mail_form=mail_form,
        form=delete_form,
        total_post_views=total_post_views,
        total_page_views=total_page_views
    )

# ======================
# ✅ ADMIN – HANTERA ANVÄNDARE
# ======================
@admin_bp.route("/manage-users", methods=["GET"])
@login_required
@roles_required("admin")
def manage_users():
    """
    Visa och filtrera användare med sökning, sortering och pagination.
    Roller visas endast för aktiva användare.
    """
    form = UserUpdateForm()
    delete_form = DeleteForm()
    search = request.args.get("search", "")
    sort_by = request.args.get("sort", "name_asc")
    page = request.args.get("page", 1, type=int)
    if page < 1:
        abort(404)

    query = User.query

    # 🔎 Filtrering och sortering
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )

    if sort_by == "name_asc":
        query = query.order_by(User.name.asc())
    elif sort_by == "name_desc":
        query = query.order_by(User.name.desc())
    elif sort_by.startswith("role_"):
        role_name = sort_by.replace("role_", "")
        query = query.join(User.roles).filter(Role.name == role_name)
    elif sort_by == "inactive":
        query = query.filter(
            (User.is_deleted.is_(True)) | (User._is_active.is_(False))
        )

    pagination = query.paginate(page=page, per_page=10)
    roles = Role.query.all()

    return render_template(
        "admin/manage_users.html",
        users=pagination.items,
        pagination=pagination,
        search=search,
        sort_by=sort_by,
        form=form,
        delete_form=delete_form,
        roles=roles
    )

@admin_bp.route('/update-users', methods=['POST'])
@login_required
@roles_required("admin")
def update_users():
    """
    Uppdatera en enskild användares namn, e-post och roller.
    Roller rensas först och tilldelas sedan på nytt.
    """
    form = UserUpdateForm()

    # ✅ Vi förväntar oss ett ID per POST
    user_id = request.form.get("update_id")
    if not user_id:
        flash("⚠️ Ingen användare markerades för uppdatering.", "warning")
        return redirect(url_for("admin.manage_users"))

    user = User.query.get(int(user_id))
    if not user:
        flash("❌ Användaren hittades inte.", "danger")
        return redirect(url_for("admin.manage_users"))

    # ✅ Uppdatera namn och e-post
    user.name = request.form.get(f'users[{user_id}][name]')
    user.email = request.form.get(f'users[{user_id}][email]')

    # ✅ Uppdatera roller
    user.roles.clear()
    selected_roles = request.form.getlist(f'users[{user_id}][roles]')
    for r in selected_roles:
        user.add_role(r)

    try:
        db.session.commit()
        flash(f"✅ Användaren '{user.name}' uppdaterades.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Något gick fel: {str(e)}", "danger")

    return redirect(url_for("admin.manage_users"))

@admin_bp.route('/delete-user/<int:user_id>', methods=["POST"])
@login_required
@roles_required("admin")
def delete_user(user_id):
    """Radera en enskild användare permanent."""
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("Användaren raderades.", "success")
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/delete-selected-users', methods=["POST"])
@login_required
@roles_required("admin")
def delete_selected_users():
    """
    Radera flera markerade användare i ett svep.
    Markerade ID skickas via checkboxes i `manage_users.html`.
    """
    selected_ids = request.form.getlist("selected_users")
    if selected_ids:
        for user_id in selected_ids:
            user = User.query.get(int(user_id))
            if user:
                db.session.delete(user)
        db.session.commit()
        flash(f"{len(selected_ids)} användare raderades.", "success")
    else:
        flash("Inga användare markerades för radering.", "warning")
    return redirect(url_for("admin.manage_users"))

@admin_bp.route("/toggle-user/<int:user_id>", methods=["POST"])
@login_required
@roles_required("admin")
def toggle_user(user_id):
    """
    Aktivera eller inaktivera ett användarkonto.
    Ej möjligt för anonymiserade (GDPR-raderade) konton.
    """
    user = User.query.get_or_404(user_id)
    if user.is_deleted:
        flash("❌ Detta konto är anonymiserat och kan inte aktiveras igen.", "danger")
        return redirect(url_for("admin.manage_users"))

    user.is_active = not user.is_active
    db.session.commit()
    flash(f"✅ Användaren {user.email} är nu {'aktiverad' if user.is_active else 'inaktiverad'}.", "success")
    return redirect(url_for("admin.manage_users"))

@admin_bp.route('/promote/<int:user_id>')
@login_required
@roles_required("admin")
def promote_user(user_id):
    """Tilldela rollen 'admin' till en användare."""
    user = User.query.get_or_404(user_id)
    user.roles.clear()
    user.add_role("admin")
    db.session.commit()
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/demote/<int:user_id>')
@login_required
@roles_required("admin")
def demote_user(user_id):
    """Ta bort admin-rättigheter från en användare (går ej på sig själv)."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Du kan inte ändra din egen roll!", "danger")
        return redirect(url_for('admin.manage_users'))
    user.roles.clear()
    user.add_role("user")
    db.session.commit()
    return redirect(url_for('admin.manage_users'))

@admin_bp.route("/create-user", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def create_user():
    """
    Skapa en ny användare manuellt.
    Skickar en länk via e-post där användaren sätter sitt eget lösenord.
    """
    form = AdminCreateUserForm()

    # ✅ Fixa NoneType-buggen: sätt en tom lista om ingen roll valts än
    if form.roles.data is None:
        form.roles.data = []

    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.strip()).first():
            flash("❌ En användare med den e-postadressen finns redan.", "danger")
            return redirect(url_for("admin.create_user"))

        new_user = User(
            email=form.email.data.strip(),
            name=form.name.data.strip(),
            password=generate_password_hash("temporary-password")
        )

        # ✅ Lägg till roller
        selected_roles = form.roles.data or []
        if selected_roles:
            for role_name in selected_roles:
                new_user.add_role(role_name)
        else:
            new_user.add_role("user")  # Standardroll

        db.session.add(new_user)
        db.session.commit()

        # Skicka e-post med lösenordslänk (som tidigare)
        token = generate_reset_token(new_user.email)
        reset_url = url_for("auth.set_password", token=token, _external=True)
        msg = Message(
            subject="Skapa ditt lösenord",
            recipients=[new_user.email],
            body=f"Hej {new_user.name},\n\nEtt konto har skapats åt dig.\n"
                 f"Skapa ditt lösenord här: {reset_url}\n\nVänliga hälsningar,\nWebbplatsen",
            sender="noreply@example.com"
        )
        mail.send(msg)

        flash(f"✅ Användare '{new_user.name}' skapad och e-post skickad.", "success")
        return redirect(url_for("admin.manage_users"))

    return render_template("admin/create_user.html", form=form)

# ======================
# ✅ ADMIN – HANTERA BLOGGINLÄGG
# ======================
@admin_bp.route("/manage-posts", methods=["GET"])
@login_required
@roles_required("admin")
def manage_posts():
    """
    Visa och hantera blogginlägg med sökning, filtrering, sortering och pagination.
    Stöd för att filtrera på kategori och publiceringsstatus.
    """
    search_query = request.args.get("search", "").strip()
    category_filter = request.args.get("category_images", "").strip()
    sort_by = request.args.get("sort", "date_desc")
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "").strip()

    posts_query = BlogPost.query

    # 🔎 Filtrering
    if search_query:
        posts_query = posts_query.filter(BlogPost.title.ilike(f"%{search_query}%"))
    if category_filter:
        posts_query = posts_query.filter(BlogPost.category_id == int(category_filter))
    if status == "published":
        posts_query = posts_query.filter(BlogPost.is_published.is_(True))
    elif status == "draft":
        posts_query = posts_query.filter(BlogPost.is_published.is_(False))

    # ↕️ Sortering
    if sort_by == "date_asc":
        posts_query = posts_query.order_by(BlogPost.created_at.asc())
    elif sort_by == "title_asc":
        posts_query = posts_query.order_by(BlogPost.title.asc())
    elif sort_by == "title_desc":
        posts_query = posts_query.order_by(BlogPost.title.desc())
    else:  # default date_desc
        posts_query = posts_query.order_by(BlogPost.created_at.desc())

    pagination = posts_query.paginate(page=page, per_page=10)

    delete_form = DeleteForm()
    all_cats = BlogCategory.query.order_by(BlogCategory.title).all()

    return render_template(
        "admin/manage_posts.html",
        posts=pagination.items,
        pagination=pagination,
        delete_form=delete_form,
        search=search_query,
        selected_category=category_filter,
        categories=all_cats,
        sort_by=sort_by,
        selected_status=status,
    )

# ======================
# ✅ ADMIN – BLOGG-KATEGORIER
# ======================
@admin_bp.route("/manage-blog-categories", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def manage_blog_categories():
    """
    Skapa, redigera och hantera bloggkategorier.
    Stöd för att byta/ta bort kategori-bild och förhindra dubbletter.
    """
    edit_id = request.args.get("edit_id", type=int)
    form = BlogCategoryForm()
    delete_form = DeleteForm()
    editing = None

    # ✏️ Fyll i formuläret vid redigering
    if edit_id:
        editing = BlogCategory.query.get_or_404(edit_id)
        if request.method == "GET":
            form.name.data = editing.name
            form.title.data = editing.title
            form.description.data = editing.description

    if form.validate_on_submit():
        if form.name.data and (not editing or form.name.data != editing.name):
            existing = BlogCategory.query.filter_by(name=form.name.data).first()
            if existing and (not editing or existing.id != editing.id):
                flash("En kategori med detta interna namn finns redan.", "danger")
                return redirect(url_for("admin.manage_blog_categories"))

        # 📂 Skapa mapp för kategori-bilder
        img_folder = os.path.img_folder = os.path.join(current_app.root_path, "..", "static", "blog_category_images")
        img_folder = os.path.abspath(img_folder)  # konverterar till absolut sökvägjoin(current_app.static_folder, "blog_category_images")
        os.makedirs(img_folder, exist_ok=True)

        if editing:
            # ✅ Uppdatera kategori
            editing.name = form.name.data
            editing.title = form.title.data
            editing.description = form.description.data

            # 🗑 Ta bort bild om begärt
            if form.delete_image.data and editing.image:
                img_path = os.path.join(current_app.static_folder, editing.image)
                if os.path.exists(img_path):
                    os.remove(img_path)
                editing.image = None

            # 🔄 Ersätt befintlig bild
            if form.replace_image.data and form.image.data:
                if editing.image:
                    old_path = os.path.join(current_app.static_folder, editing.image)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                # Generera unikt namn
                filename = f"{uuid.uuid4().hex}.webp"
                img_path = os.path.join(img_folder, filename)

                # Öppna och konvertera till webp
                image = Image.open(form.image.data)
                image.save(img_path, format="WEBP")

                # Spara webbadress till databasen
                editing.image = f"blog_category_images/{filename}"

            # ➕ Ny bild om ingen tidigare fanns
            if not editing.image and form.image.data:
                # Generera unikt namn
                filename = f"{uuid.uuid4().hex}.webp"
                img_path = os.path.join(img_folder, filename)

                # Öppna och konvertera till webp
                image = Image.open(form.image.data)
                image.save(img_path, format="WEBP")

                # Spara webbadress till databasen
                editing.image = f"blog_category_images/{filename}"

            db.session.commit()
            flash("Kategorin har uppdaterats.", "success")

        else:
            # ✅ Skapa ny kategori
            new_cat = BlogCategory(
                name=form.name.data,
                title=form.title.data,
                description=form.description.data
            )
            if form.image.data:
                filename = secure_filename(form.image.data.filename)
                path = os.path.join(img_folder, filename)
                form.image.data.save(path)
                new_cat.image = f"blog_category_images/{filename}"
            db.session.add(new_cat)
            db.session.commit()
            flash("Kategori skapad.", "success")

        return redirect(url_for("admin.manage_blog_categories"))

    categories = BlogCategory.query.order_by(BlogCategory.title).all()
    return render_template("admin/manage_blog_categories.html", form=form, categories=categories, delete_form=delete_form, editing=editing, show_back_button=True)

@admin_bp.route("/admin/delete-category/<int:category_id>", methods=["POST"])
@login_required
@roles_required("admin")
def delete_blog_category(category_id):
    """
    Radera en bloggkategori (endast om den saknar inlägg).
    Eventuell bild tas bort från filsystemet.
    """
    category = BlogCategory.query.get_or_404(category_id)
    if category.posts:
        flash("Kategorin innehåller inlägg och kan inte raderas.", "danger")
    else:
        db.session.delete(category)
        db.session.commit()
        flash("Kategorin har raderats.", "success")
    return redirect(url_for("admin.manage_blog_categories"))

# ======================
# ✅ ADMIN – HANTERA KOMMENTARER
# ======================
@admin_bp.route('/comments', methods=["GET", "POST"])
@login_required
@roles_required("admin")
def manage_comments():
    """
    Visa, filtrera och hantera alla kommentarer.
    Stöd för flaggning, redigering, godkännande och radering.
    """
    search = request.args.get("search", "").strip()
    post_filter = request.args.get("post_filter", "").strip()
    page = request.args.get("page", 1, type=int)
    if page < 1:
        abort(404)
    per_page = 10

    # 🔗 Join för att kunna söka på användarnamn och blogginläggstitlar
    query = Comment.query.join(BlogPost).join(User)

    # 🔎 Filtrering
    if search:
        query = query.filter(
            (Comment.text.ilike(f"%{search}%")) |
            (Comment.comment_author.has(User.name.ilike(f"%{search}%"))) |
            (Comment.post.has(BlogPost.title.ilike(f"%{search}%")))
        )

    if post_filter:
        query = query.filter(BlogPost.title == post_filter)

    pagination = query.order_by(Comment.id.desc()).paginate(page=page, per_page=per_page)
    comments = pagination.items
    delete_form = DeleteForm()

    # 🟢 Formulär för att avflagga markerade kommentarer
    unflag_forms = {comment.id: ApproveForm() for comment in comments}

    # ✏️ Formulär för att redigera kommentarstext
    edit_forms = {}
    for comment in comments:
        # Skapa CommentForm-instansen
        form_instance = CommentForm()
        # Sätt manuellt värdet för 'comment_text' fältet till 'comment.text'
        form_instance.comment_text.data = comment.text
        edit_forms[comment.id] = form_instance
    # =================================

    unique_posts = [title for (title,) in db.session.query(BlogPost.title).distinct().all()]

    return render_template(
        "admin/manage_comments.html",
        comments=comments,
        delete_form=delete_form,
        unflag_forms=unflag_forms,
        unique_posts=unique_posts,
        pagination=pagination,
        search=search,
        post_filter=post_filter,
        edit_forms=edit_forms # Fortfarande viktigt att skicka denna
    )

# ======================
# ✅ ADMIN – MASSHANTERING AV KOMMENTARER
# ======================
@admin_bp.route("/comments/actions", methods=["POST"])
@login_required
@roles_required("admin")
def handle_comment_actions():
    """
    Hantera massåtgärder för markerade kommentarer:
    - Radera flera samtidigt
    - Flagga eller godkänna enstaka kommentarer
    """
    action = request.form.get("action")
    selected_ids = request.form.getlist("selected_comments")

    if action == "delete":
        if not selected_ids:
            flash("Inga kommentarer markerades för radering.", "warning")
        else:
            for comment_id in selected_ids:
                comment = db.session.get(Comment, int(comment_id))
                if comment:
                    db.session.delete(comment)
            db.session.commit()
            flash(f"{len(selected_ids)} kommentar(er) raderades.", "success")

    elif action and action.startswith("approve_"):
        comment_id = int(action.split("_")[1])
        comment = db.session.get(Comment, comment_id)
        if comment:
            comment.flagged = False
            comment.visible = True
            db.session.commit()
            flash("Kommentaren är nu godkänd.", "success")

    elif action and action.startswith("flag_"):
        comment_id = int(action.split("_")[1])
        comment = db.session.get(Comment, comment_id)
        if comment:
            comment.flagged = True
            comment.visible = False
            db.session.commit()
            flash("Kommentaren har markerats som olämplig.", "warning")

    return redirect(url_for("admin.manage_comments"))

# ======================
# ✅ ADMIN – REDIGERA EN KOMMENTAR
# ======================
@admin_bp.route('/comments/edit/<int:comment_id>', methods=["POST"])
@login_required
@roles_required("admin")
def edit_comment(comment_id):
    """
    Uppdatera texten i en specifik kommentar.
    Lägger även till tidsstämpel för senaste uppdatering.
    """
    comment = Comment.query.get_or_404(comment_id)
    comment.text = request.form.get("text")
    comment.updated_at = datetime.now(ZoneInfo("Europe/Stockholm"))
    db.session.commit()
    flash("Kommentaren har uppdaterats.", "success")
    return redirect(url_for("admin.manage_comments"))

# ======================
# ✅ ADMIN – FLAGGHANTERING & RADERING
# ======================
@admin_bp.route('/unflag-comment/<int:comment_id>', methods=['POST'])
@login_required
@roles_required("admin")
def unflag_comment(comment_id):
    """
    Ta bort flaggning från en kommentar (synliggör den igen).
    """
    comment = Comment.query.get_or_404(comment_id)
    comment.flagged = False
    db.session.commit()
    flash("Kommentaren har avflaggats.", "success")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/delete-comment/<int:comment_id>', methods=['POST'])
@login_required
@roles_required("admin")
def delete_comment(comment_id):
    """
    Radera en enskild kommentar (utan att gå via masshantering).
    """
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash("Kommentaren har raderats.", "success")
    return redirect(url_for('admin.admin_dashboard'))


from math import ceil
# ======================
# ✅ ADMIN – VISA OCH HANTERA UPPLADDADE BILDER
# ======================
@admin_bp.route("/manage-uploads")
@login_required
@roles_required("admin")
def manage_uploads():
    """
    Visa alla uppladdade bilder (blogg, portfolio, kategorier).
    Stöd för sortering, filtrering och sidvisning.
    """
    static_path = current_app.static_folder
    page = request.args.get("page", 1, type=int)
    if page < 1:
        abort(404)
    per_page = 12
    selected_folder = request.args.get("folder")
    sort_by = request.args.get("sort", "name_asc")

    # ✅ Mappstruktur för olika bildkategorier
    image_dirs = {
        "blog_category_images": os.path.join(static_path, "blog_category_images"),
        "portfolio_category_images": os.path.join(static_path, "portfolio_category_images"),
        "uploads/blog": os.path.join(static_path, "uploads", "blog"),
        "uploads/portfolio": os.path.join(static_path, "uploads", "portfolio"),
    }

    all_images = []
    for label, path in image_dirs.items():
        if os.path.exists(path):
            for filename in os.listdir(path):
                if filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    display_name = filename if len(filename) <= 25 else filename[:22] + "..."
                    all_images.append({
                        "folder": label,
                        "filename": filename,
                        "url": f"{label}/{filename}",
                        "name": display_name
                    })

    # ✅ Filtrera på vald mapp
    if selected_folder:
        filtered_images = [img for img in all_images if img["folder"] == selected_folder]
    else:
        filtered_images = all_images

    # ✅ Sortering
    if sort_by == "name_asc":
        filtered_images.sort(key=lambda x: x["filename"].lower())
    elif sort_by == "name_desc":
        filtered_images.sort(key=lambda x: x["filename"].lower(), reverse=True)

    # ✅ Paginering
    total = len(filtered_images)
    total_pages = ceil(total / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    images = filtered_images[start:end]

    # ✅ Lista alla unika mappar för dropdown i UI
    folders = sorted(set(img["folder"] for img in all_images))

    # ✅ Skapa delete-formulär per bild
    delete_forms = {
        f"{img['folder']}/{img['filename']}": ImageDeleteForm(folder=img["folder"], filename=img["filename"])
        for img in images
    }

    # ✅ Mappning för att visa kategori utifrån filnamn (portfolio)
    category_mapping = {
        c.image: c.name for c in Category.query.all() if c.image
    }

    return render_template(
        "admin/manage_uploads.html",
        images=images,
        folders=folders,
        selected_folder=selected_folder,
        sort_by=sort_by,
        delete_forms=delete_forms,
        page=page,
        total_pages=total_pages,
        total_images=total,
        category_mapping=category_mapping  # Skickas till mallen
    )

# ======================
# ✅ ADMIN – RADERA EN BILD
# ======================
@admin_bp.route('/uploads/delete', methods=["POST"])
@login_required
@roles_required("admin")
def delete_upload():
    """
    Radera en enskild uppladdad bild från servern.
    """
    form = ImageDeleteForm()
    if form.validate_on_submit():
        folder = form.folder.data
        filename = form.filename.data

        static_path = current_app.static_folder
        full_path = os.path.join(static_path, folder, filename)

        if os.path.exists(full_path):
            os.remove(full_path)
            flash(f"{filename} raderades från {folder}.", "success")
        else:
            flash(f"Filen {filename} hittades inte i {folder}.", "danger")

        return redirect(url_for("admin.manage_uploads"))
    else:
        flash("Fel vid formulärvalidering – kunde inte radera bild.", "danger")
        return redirect(url_for("admin.manage_uploads"))

# ======================
# ✅ ADMIN – RENSNING AV OANVÄNDA BILDER (BLOGG)
# ======================
@admin_bp.route("/cleanup-images")
@login_required
@roles_required("admin")
def cleanup_unused_images():
    """
    Rensa bort oanvända bilder i blogg-mappen.
    Jämför mot bilder som används i inlägg (img_url och Quill-body).
    """
    upload_folder = os.path.join(current_app.static_folder, "uploads", "blog")
    removed = []

    if not os.path.exists(upload_folder):
        flash("Uppladdningsmappen för blogg finns inte.", "warning")
        return redirect(url_for("admin.manage_posts"))

    # Samla alla använda bilder från img_url och Quill
    used_images = set()

    # 1. Från img_url (huvudbild på inlägget)
    for post in BlogPost.query.all():
        if post.img_url:
            used_images.add(post.img_url.replace("uploads/blog/", ""))

        # 2. Från Quill-body: plocka ut img src från HTML
        if post.body:
            matches = re.findall(r'src="/static/uploads/blog/([^"]+)"', post.body)
            used_images.update(matches)

    # 3. Jämför med filerna i mappen och rensa bort bilder som inte används
    for filename in os.listdir(upload_folder):
        if filename not in used_images:
            try:
                os.remove(os.path.join(upload_folder, filename))
                removed.append(filename)
            except Exception as e:
                current_app.logger.warning(f"Kunde inte radera {filename}: {e}")

    flash(f"{len(removed)} oanvända bilder raderades.", "info")
    return redirect(url_for("admin.manage_posts"))

# ======================
# ✅ ADMIN – HANTERA PORTFOLIO-KATEGORIER
# ======================
@admin_bp.route("/manage-portfolio-categories", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def manage_portfolio_categories():
    """
    Hantera kategorier för portfolio-inlägg:
    - Skapa nya kategorier
    - Redigera befintliga kategorier
    - Ladda upp eller ta bort kategori-bilder
    """
    edit_id = request.args.get("edit_id", type=int) # ID för kategori som ska redigeras (om någon)
    form = CategoryForm()                           # Formulär för att skapa/redigera kategori
    image_delete_form = DeleteForm()
    delete_form = DeleteForm()                      # Formulär för att radera kategori
    editing = None                                  # Håller info om kategori som redigeras

    # ✅ Om en kategori ska redigeras – hämta den
    if edit_id:
        editing = Category.query.get_or_404(edit_id)
        if request.method == 'GET':
            form.name.data = editing.name
            form.title.data = editing.title
            form.description.data = editing.description

    if form.validate_on_submit():
        # ✅ Kontrollera att kategorinamnet inte redan finns
        if form.name.data and (not editing or form.name.data != editing.name):
            existing = Category.query.filter_by(name=form.name.data).first()
            if existing and existing.id != (editing.id if editing else None):
                flash("En kategori med detta interna namn finns redan.", "danger")
                return redirect(url_for("admin.manage_portfolio_categories"))

        # ✅ Förbered mapp för att lagra kategori-bilder
        img_folder = os.path.join(current_app.static_folder, "portfolio_category_images")
        os.makedirs(img_folder, exist_ok=True)

        if editing:
            # ✅ Uppdatera kategori-attribut
            editing.name = form.name.data
            editing.title = form.title.data
            editing.description = form.description.data

            # ✅ Radera tidigare bild om admin väljer "Ta bort bild"
            if form.delete_image.data and editing.image:
                img_path = os.path.join(current_app.static_folder, editing.image)
                if os.path.exists(img_path):
                    os.remove(img_path)
                editing.image = None

            # ✅ Byt ut tidigare bild om en ny laddas upp
            if form.replace_image.data and form.image.data:
                if editing.image:
                    old_path = os.path.join(current_app.static_folder, editing.image)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                filename = secure_filename(form.image.data.filename)
                img_path = os.path.join(img_folder, filename)
                form.image.data.save(img_path)
                editing.image = f"portfolio_category_images/{filename}"

            # ✅ Tillåt ny uppladdning om ingen bild fanns innan
            if not editing.image and form.image.data:
                filename = secure_filename(form.image.data.filename)
                img_path = os.path.join(img_folder, filename)
                form.image.data.save(img_path)
                editing.image = f"portfolio_category_images/{filename}"

            db.session.commit()
            flash("Kategorin har uppdaterats.", "success")

        else:
            # ✅ Skapa ny kategori
            new_cat = Category(
                name=form.name.data,
                title=form.title.data,
                description=form.description.data
            )
            if form.image.data:
                filename = secure_filename(form.image.data.filename)
                path = os.path.join(img_folder, filename)
                form.image.data.save(path)
                new_cat.image = f"portfolio_category_images/{filename}"

            db.session.add(new_cat)
            db.session.commit()
            flash("Kategori skapad.", "success")

        return redirect(url_for("admin.manage_portfolio_categories"))

    # ✅ Hämta alla kategorier för visning i tabell
    categories = Category.query.order_by(Category.title).all()
    return render_template("admin/manage_portfolio_categories.html",
                           form=form,
                           categories=categories,
                           delete_form=delete_form,
                           editing=editing)

# ======================
# ✅ ADMIN – RADERA EN PORTFOLIO-KATEGORI
# ======================
@admin_bp.route("/delete-portfolio-category/<int:category_id>", methods=["POST"])
@login_required
@roles_required("admin")
def delete_portfolio_category(category_id):
    """
    Radera en portfolio-kategori:
    - Endast om den inte innehåller portfolio-inlägg
    - Tar även bort bildfilen om den finns
    """
    category = Category.query.get_or_404(category_id)

    # Kontrollera om kategorin har kopplade portfolio-items
    if category.items:
        flash("Kategorin innehåller portfolio-inlägg och kan inte raderas.", "danger")
        return redirect(url_for("admin.manage_portfolio_categories"))
    else:
        # Om kategorin har en bild kopplad, radera bilden först
        if category.image:
            img_path = os.path.join(current_app.static_folder, category.image)
            if os.path.exists(img_path):
                os.remove(img_path)
                current_app.logger.info(f"Raderade kategoribild: {img_path}")  # Lägg till loggning

        db.session.delete(category)
        db.session.commit()
        flash("Kategorin har raderats.", "success")
    return redirect(url_for("admin.manage_portfolio_categories"))

# ======================
# ✅ ADMIN – HANTERA PORTFOLIO-INLÄGG
# ======================
@admin_bp.route("/manage-portfolio-item")
@login_required
def manage_portfolio_item():
    """
    Visa och hantera portfolio-inlägg.
    Stöd för sökning, kategorifilter, statusfilter och sortering.
    """
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "")

    if page < 1:
        abort(404)
    search = request.args.get("search", "", type=str)
    selected_category = request.args.get("category", "", type=str)
    sort_by = request.args.get("sort", "date_desc", type=str)

    query = PortfolioItem.query

    # ✅ Filtrering på titel
    if search:
        query = query.filter(PortfolioItem.title.ilike(f"%{search}%"))

    # ✅ Filtrering på kategori
    if selected_category:
        query = query.filter(PortfolioItem.category_id == int(selected_category))

    # ✅ Filtrering på status (publicerad/utkast)
    if status == "published":
        query = query.filter(PortfolioItem.is_published == True)
    elif status == "draft":
        query = query.filter(PortfolioItem.is_published == False)

    # ✅ Sorteringsalternativ
    sort_options = {
        "date_desc": PortfolioItem.date.desc(),
        "date_asc": PortfolioItem.date.asc(),
        "title_asc": asc(PortfolioItem.title),
        "title_desc": desc(PortfolioItem.title),
    }
    query = query.order_by(sort_options.get(sort_by, PortfolioItem.date.desc()))

    pagination = query.paginate(page=page, per_page=10)
    items = pagination.items

    # ✅ Hämta unika kategorier för filter-dropdown
    categories = Category.query.order_by(Category.title).all()

    return render_template(
        "admin/manage_portfolio_item.html",
        items=items,
        pagination=pagination,
        search=search,
        selected_category=selected_category,
        selected_status=status,
        sort_by=sort_by,
        categories=categories,
        delete_form=DeleteForm()
    )

# ======================
# ✅ ADMIN – MASSRADERA PORTFOLIO-INLÄGG
# ======================
@admin_bp.route("/bulk-delete-portfolio", methods=["POST"])
@login_required
@roles_required("admin")
def bulk_delete_portfolio():
    """
    Massradera valda portfolio-inlägg.
    Tar bort varje markerat inlägg enskilt.
    """
    ids = request.form.getlist("selected_items")
    if ids:
        for item_id in ids:
            item = PortfolioItem.query.get(item_id)
            if item:
                db.session.delete(item)  # 🗑 Ta bort varje portfolio-inlägg
        db.session.commit()
        flash(f"{len(ids)} inlägg raderade.", "success")
    else:
        flash("Inga inlägg valda.", "warning")
    return redirect(url_for("admin.manage_portfolio_item"))

# ======================
# ✅ ADMIN – MASSRADERA BLOGGINLÄGG
# ======================
@admin_bp.route("/bulk-delete-posts", methods=["POST"])
@login_required
@roles_required("admin")
def bulk_delete_posts():
    """
    Massradera valda blogginlägg.
    Tar bort varje markerat blogginlägg enskilt.
    """
    ids = request.form.getlist("selected_items")
    if ids:
        for post_id in ids:
            post = BlogPost.query.get(post_id)
            if post:
                db.session.delete(post)
        db.session.commit()
        flash(f"{len(ids)} blogginlägg raderade.", "success")
    else:
        flash("Inga inlägg valda.", "warning")
    return redirect(url_for("admin.manage_posts"))

# ======================
# ✅ ADMIN – MANUELLT SKICKA BLOGGMAILS
# ======================
@admin_bp.route("/send-blog-mails", methods=["POST"])
@login_required
@roles_required("admin")
def trigger_blog_mail():
    """
    Manuell körning av schemalagda bloggmails (max 10 åt gången).
    Använder samma funktion som schemalagd automatisk körning.
    """
    try:
        check_and_send_blog_emails()  # ✅ Kallar på funktionen i utils.py
        flash("✅ Bloggmail har skickats (max 10 utskick).", "success")
    except Exception as e:
        current_app.logger.error(f"❌ Manuell mailkörning misslyckades: {e}")
        flash("❌ Ett fel uppstod vid försök att skicka mail.", "danger")
    return redirect(url_for("admin.admin_dashboard"))

# ======================
# ✅ ADMIN – VISA STATISTIK (BLOGG, SIDOR & PORTFOLIO)
# ======================
@admin_bp.route("/views")
@login_required
@roles_required("admin")
def view_statistics():
    """
    Visa statistik för visningar av:
    - Blogginlägg (sorterade efter flest visningar)
    - Vanliga sidor (sorterade efter flest visningar)
    - Portfolio (inklusive totalantal för portfolio)
    """

    # ✅ Hämta alla blogginlägg sorterade efter visningar (högst först)
    blog_posts = BlogPost.query.order_by(BlogPost.views.desc()).all()

    # ✅ Hämta alla vanliga sidor (exkluderar portfolio)
    pages = PageView.query.filter(PageView.page.notlike("portfolio_%")).order_by(PageView.views.desc()).all()

    portfolio_views = PageView.query.filter(PageView.page.like("portfolio_%")).order_by(PageView.views.desc()).all()
    portfolio_data = []          # Lista med {"title": ..., "views": ...}
    total_portfolio_views = 0    # Summerar alla visningar på portfolio

    # ✅ Loopar genom portfolio-sidor och hämtar titlar
    for view in portfolio_views:
        item_id = view.page.split("_")[1]                           # Exempel: "portfolio_5" → ID = 5
        item = PortfolioItem.query.get(item_id)
        if item:
            portfolio_data.append({"title": item.title,             # Namn på portfolio-inlägget
                                   "views": view.views})            # Antal visningar
            total_portfolio_views += view.views                     # ✅ Addera till totalen

    # ✅ Mappning för att visa svenska namn på sidor
    page_name_map = {
        "home": "Startsida",
        "about": "Om sidan",
        "cv": "Curriculum vitae",
        "contact": "Kontakt",
        "portfolio": "Portfolio",
        "blog": "Blogg"
    }

    # ✅ Mappning för att länka sidorna korrekt
    page_url_map = {
        "home": url_for("pages.home"),
        "about": url_for("pages.about"),
        "cv": url_for("pages.cv"),
        "contact": url_for("pages.contact"),
        "portfolio": url_for("portfolio.index"),
        "blog": url_for("blog.index"),
    }

    return render_template(
        "admin/view_statistics.html",
        blog_posts=blog_posts,
        pages=pages,
        portfolio_data=portfolio_data,
        total_portfolio_views=total_portfolio_views,
        page_name_map=page_name_map,      # ✅ Skickar mappning av sidnamn
        page_url_map=page_url_map         # ✅ Skickar URL-mappning
    )
