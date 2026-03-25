# app/blog/blog.py
# ================================================
# ✅ IMPORTER & KONFIGURATION
# ================================================
import os
import uuid
import logging
import pytz
from math import ceil
from PIL import Image
from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, current_app, flash, request, abort, jsonify
from flask_login import login_required, current_user
from babel.dates import format_datetime

from app.blog.utils import notify_subscribers
from app.decorators import roles_required
from app.extensions import db, csrf, mail
from app.forms import BlogPostForm, CommentForm, DeleteForm, CategorySelectForm, CategoryFilterForm, BlogCategoryForm
from app.models import BlogPost, Comment, User, BlogCategory, Role
from app.utils.time import get_local_now, DEFAULT_TZ
from app.utils.image_utils import save_image, delete_existing_image, _handle_quill_upload
from app.utils.helpers import sanitize_html
from app.utils.views import increment_post_views

# ✅ Flask Blueprint för bloggen
blog_bp = Blueprint('blog', __name__, url_prefix='/blog')

logger = logging.getLogger(__name__)  # Loggning

POSTS_PER_PAGE = 12
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024
MAX_SIZE_MB = 10

# ================================================
# ✅ HJÄLPFUNKTIONER
# ================================================
def allowed_file(filename):
    """Kontrollera om filen har en tillåten filändelse."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ================================================
# ✅ ROUTER – VISA BLOGGINLÄGG
# ================================================
@blog_bp.route("/")
@blog_bp.route("/page/<int:page>")
def index(page=1):
    """
    Lista alla publicerade blogginlägg:
    - Sök, filtrera och sortera
    - Paginering
    """
    POSTS_PER_PAGE = 12

    sort_order = request.args.get("sort", "desc")
    search_term = request.args.get("search", "").strip()
    category_filter = request.args.get("category", type=int)

    # Bas‐query: bara publicerade inlägg
    now = get_local_now()
    base_q = BlogPost.query.filter(BlogPost.created_at <= now)

    # Hämta alla riktiga kategorier ur blog_categories
    cats = BlogCategory.query.order_by(BlogCategory.title).all()
    # Gör listan av (id, titel)
    real_choices = [(c.id, c.title) for c in cats]

    # Sätt 0 som “ingen filter” istället för ""
    choices = [(0, "Alla kategorier")] + real_choices

    category_form = CategoryFilterForm()
    category_form.category.choices = choices

    # Applicera kategori‐filter om valt, Läs in som int, default 0
    category_filter = request.args.get("category", 0, type=int)
    if category_filter:
        base_q = base_q.filter(BlogPost.category_id == category_filter)

    # Applicera sök-filter om satt
    if search_term:
        base_q = base_q.filter(
            db.or_(
                BlogPost.title.ilike(f"%{search_term}%"),
                BlogPost.subtitle.ilike(f"%{search_term}%"),
                BlogPost.body.ilike(f"%{search_term}%"),
            )
        )

    # Sortering
    order_func = BlogPost.created_at.asc() if sort_order == "asc" else BlogPost.created_at.desc()
    base_q = base_q.order_by(order_func)

    # Paginering
    total_posts = base_q.count()
    posts = (base_q
             .offset((page - 1) * POSTS_PER_PAGE)
             .limit(POSTS_PER_PAGE)
             .all())
    total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE

    # Radera‐formulär
    delete_form = DeleteForm()

    # Rendera templaten
    return render_template(
        "blog/blog.html",
        posts=posts,
        page=page,
        total_pages=total_pages,
        sort_order=sort_order,
        category_form=category_form,
        current_category=category_filter,
        delete_form=delete_form
    )

@blog_bp.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    """
    Visa ett specifikt blogginlägg:
    - Visa kommentarer
    - Låt användare skriva nya kommentarer
    - Visa relaterade senaste inlägg
    """
    post = BlogPost.query.get_or_404(post_id)
    now = get_local_now()

    # ✅ Databastiderna är redan i UTC (inget behov av manuell konvertering här)
    # Konverteringen till lokal tid sker i templates via format_datetime_sv-filtret

    # Ladda senaste inlägg för sidfoten
    recent_query = (BlogPost.query
                    .filter(BlogPost.id != post_id)
                    .filter(BlogPost.created_at <= now)
                    .order_by(BlogPost.created_at.desc()))

    recent_page = request.args.get("recent_page", 1, type=int)
    per_page = 5
    total = recent_query.count()
    total_pages = (total + per_page - 1) // per_page
    recent_posts = recent_query.offset((recent_page - 1) * per_page).limit(per_page).all()
    increment_post_views(post)  # ✅ Öka visningsräknaren

    comment_form = CommentForm()
    delete_form = DeleteForm()

    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            abort(401)
        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            post=post
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('blog.show_post', post_id=post.id))

    return render_template('blog/post.html',
                           post=post,
                           now=now,
                           comment_form=comment_form,
                           delete_form=delete_form,
                           recent_posts=recent_posts,
                           recent_page=recent_page,
                           recent_total_pages=total_pages)

# ================================================
# ✅ ROUTER – SKAPA NYTT BLOGGINLÄGG
# ================================================



@blog_bp.route("/new_post", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def new_post():
    """
    Skapa ett nytt blogginlägg:
    - Hanterar bild (konverterar till WEBP)
    - Hanterar datum/tid (formulärdata → UTC för databas)
    - Skickar notis till prenumeranter
    """
    form = BlogPostForm()
    cats = BlogCategory.query.order_by(BlogCategory.title).all()
    form.category.choices = [(c.id, c.title) for c in cats]

    if form.validate_on_submit():
        # --- Bildhantering ---
        img_url = "assets/img/default_blog_category.webp"
        if form.img_file.data:
            try:
                filename = save_image(form.img_file.data, folder="uploads/blog")
                img_url = f"uploads/blog/{filename}"
            except Exception as e:
                current_app.logger.error(f"Fel vid bildhantering: {e}")
                flash("Ett fel uppstod vid bildhantering. Använder standardbild.", "warning")

        # --- Datum- och tidslogik (NY FÖRENKLAD VERSION) ---
        from app.utils.time import parse_form_datetime
        
        try:
            # Konvertera formulärdata (datum + tid) direkt till UTC
            post_created_at_utc = parse_form_datetime(
                str(form.date.data),  # YYYY-MM-DD
                form.time.data        # HH:MM
            )
        except ValueError as e:
            flash(f"Ogiltigt datum/tid-format: {e}", "danger")
            return render_template("blog/new_post.html", form=form)

        # --- Skapa nytt inlägg ---
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=sanitize_html(form.body.data),
            created_at=post_created_at_utc,  # ✅ Sparar i UTC
            updated_at=None,
            img_url=img_url,
            category_id=form.category.data,
            author=current_user
        )

        db.session.add(new_post)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Fel vid databasoperation: {e}")
            flash("Ett fel uppstod när inlägget skulle sparas.", "danger")
            return render_template("blog/new_post.html", form=form)

        # ✅ Inlägget är sparat!
        # 📧 Mail skickas automatiskt av bakgrundsschedulern när publiceringsdatum passerat
        
        # Visa rätt meddelande beroende på när inlägget publiceras
        now_utc = datetime.now(pytz.utc)
        if post_created_at_utc <= now_utc:
            flash("✅ Nytt inlägg har publicerats!", "success")
        else:
            # Konvertera till lokal tid för att visa användaren
            from app.utils.time import DEFAULT_TZ
            local_time = post_created_at_utc.astimezone(DEFAULT_TZ).strftime('%Y-%m-%d kl. %H:%M')
            flash(f"📅 Inlägg schemalagt för publicering: {local_time}", "info")

        return redirect(url_for("blog.index"))

    return render_template("blog/new_post.html", form=form)


# ================================================
# ✅ ROUTER – REDIGERA BLOGGINLÄGG
# ================================================
@blog_bp.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def edit_post(post_id):
    """
    Redigera befintligt blogginlägg:
    - Kan byta/radera bild
    - Uppdaterar updated_at om något ändras
    """
    post = BlogPost.query.get_or_404(post_id)

    from app.utils.time import get_display_time
    
    # ✅ Konvertera UTC-tid från databas till lokal tid för formuläret
    local_created_at = get_display_time(post.created_at)
    
    form = BlogPostForm(
        obj=post,
        date=local_created_at.date(),
        time=local_created_at.strftime('%H:%M')
    )

    cats = BlogCategory.query.order_by(BlogCategory.title).all()
    form.category.choices = [(c.id, c.title) for c in cats]

    if request.method == "GET":
        form.category.data = post.category_id

    if form.validate_on_submit():
        # --- Radera gammal bild ---
        if form.delete_image.data and post.img_url and post.img_url != "assets/img/default_blog_category.webp":
            try:
                delete_existing_image(post.img_url, folder="")
            except Exception as e:
                current_app.logger.error(f"Fel vid radering av bild: {e}")
                flash("Kunde inte ta bort bilden.", "warning")
            post.img_url = "assets/img/default_blog_category.webp"

        # --- Ny bild ---
        if form.img_file.data:
            try:
                delete_existing_image(post.img_url, folder="")
                filename = save_image(form.img_file.data, folder="uploads/blog")
                post.img_url = f"uploads/blog/{filename}"
            except Exception as e:
                current_app.logger.error(f"Fel vid ny bilduppladdning: {e}")
                flash("Fel vid bilduppladdning.", "warning")

        # --- Uppdatera text och metadata ---
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.body = sanitize_html(form.body.data)
        post.category_id = form.category.data
        
        # Sätt alltid updated_at när man redigerar
        post.updated_at = get_local_now()

        try:
            db.session.commit()
            flash("Inlägget har uppdaterats.", "success")
            return redirect(url_for("blog.show_post", post_id=post.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Fel vid uppdatering: {e}")
            flash("Fel vid sparning. Kontrollera loggarna.", "danger")

    return render_template("blog/edit_blog.html", form=form, post=post)


# ================================================
# ✅ ROUTER – RADERA BLOGGINLÄGG
# ================================================
@blog_bp.route('/delete/<int:post_id>', methods=['POST'])
@login_required
@roles_required("admin")
def delete_post(post_id):
    """
    Radera ett blogginlägg (endast admin).
    """
    post = BlogPost.query.get_or_404(post_id)

    if not current_user.has_role("admin"):
        abort(403)

    db.session.delete(post)
    db.session.commit()
    flash("Inlägget raderades.", "info")
    return redirect(url_for("blog.index"))

# ================================================
# ✅ ROUTER – LADDA UPP BILD VIA EDITOR (t.ex. Quill)
# ================================================
@blog_bp.route('/upload', methods=['POST'])
@login_required
@roles_required("admin")
@csrf.exempt
def upload_image():
    """
    Ladda upp en bild via editor (t.ex. Quill):
    - Konverterar alltid till WEBP
    - Sätter unik fil med timestamp
    """
    file = request.files.get("image")

    if not file or not allowed_file(file.filename):
        logger.warning(f"Ogiltig eller saknad fil: {file.filename if file else 'Ingen fil'}")
        return jsonify({'error': 'Ingen giltig bild'}), 400

    file_content = file.read()
    if len(file_content) > current_app.config.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024):
        logger.warning(f"Filen är för stor: {len(file_content)} bytes")
        return jsonify({'error': 'Filen är för stor'}), 400

    try:
        from io import BytesIO
        from datetime import datetime
        image = Image.open(BytesIO(file_content)).convert("RGB")

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{uuid.uuid4().hex}.webp"

        upload_dir = os.path.join(current_app.static_folder, "uploads", "blog")
        os.makedirs(upload_dir, exist_ok=True)

        full_path = os.path.join(upload_dir, filename)
        image.save(full_path, "WEBP", quality=85)

        image_url = url_for('static', filename=f"uploads/blog/{filename}")
        logger.info(f"Bild uppladdad och konverterad: {image_url}")
        return jsonify({'url': image_url})

    except Exception as e:
        logger.exception(f"Fel vid bildhantering: {e}")
        return jsonify({'error': 'Fel vid konvertering eller sparning'}), 500

# ================================================
# ✅ ROUTER – VISA INLÄGG EFTER KATEGORI
# ================================================
@blog_bp.route("/category/<slug>")
@blog_bp.route("/category/<slug>/page/<int:page>")
def posts_by_category(slug, page=1):
    """
    Visa blogginlägg filtrerade på en specifik kategori:
    - Filtrerar via kategori-slug
    - Stöd för paginering
    - Sorteringsval (asc/desc)
    """
    # --- Hämta kategori baserat på slug ---
    category = BlogCategory.query.filter_by(slug=slug).first_or_404()

    # --- Hämta sorteringsordning (default: senaste först) ---
    sort_order = request.args.get('sort', 'desc')  # 'desc' som standard

    # --- Filtrera inlägg på kategori ---
    query = BlogPost.query.filter_by(category=category)
    query = query.order_by(
        BlogPost.created_at.asc() if sort_order == 'asc' else BlogPost.created_at.desc()
    )

    # --- Paginering ---
    total_posts = query.count()
    start = (page - 1) * POSTS_PER_PAGE
    posts = query.slice(start, start + POSTS_PER_PAGE).all()
    total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE

    # --- Rendera kategorisida ---
    return render_template("blog/layout.html", posts=posts, category=category,
                           page=page, total_pages=total_pages, sort_order=sort_order)