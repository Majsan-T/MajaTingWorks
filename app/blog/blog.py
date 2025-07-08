# app/blog/blog.py
import os
from flask import Blueprint, render_template, redirect, url_for, current_app, flash, request, abort, jsonify
from flask_login import login_required, current_user
from flask_mail import Message
from app import mail
from app.blog.utils import notify_subscribers
from app.decorators import admin_only
from app.extensions import db, csrf
from app.forms import BlogPostForm, CommentForm, DeleteForm, CategorySelectForm, CategoryFilterForm, BlogCategoryForm
from app.models import BlogPost, Comment, User, BlogCategory
from app.utils.time import get_local_now, DEFAULT_TZ
from app.utils.image_utils import save_image, delete_existing_image, _handle_quill_upload
from app.utils.helpers import get_local_now, sanitize_html, DEFAULT_TZ
from babel.dates import format_datetime
import datetime
from datetime import datetime, time, timezone
from PIL import Image
from werkzeug.utils import secure_filename
from zoneinfo import ZoneInfo
import uuid
import logging # För att logga händelser
import pytz
from math import ceil

blog_bp = Blueprint('blog', __name__, url_prefix='/blog')
logger = logging.getLogger(__name__) # Hämta logger för denna modul
utc_dt = datetime.utcnow().replace(tzinfo=pytz.utc)
stockholm_time = utc_dt.astimezone(pytz.timezone("Europe/Stockholm"))
formatted = format_datetime(stockholm_time, locale='sv_SE')

POSTS_PER_PAGE = 12

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024
MAX_SIZE_MB = 10

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def handle_image_upload(img_file):
    if not img_file or img_file.filename == "":
        return ""

    original_filename = secure_filename(img_file.filename)
    filename_base, _ = os.path.splitext(original_filename)
    new_filename = f"{filename_base}.webp"

    upload_folder = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    temp_path = os.path.join(upload_folder, original_filename)
    file_path = os.path.join(upload_folder, new_filename)

    try:
        img_file.save(temp_path)
        image = Image.open(temp_path)
        max_width = 800
        if image.width > max_width:
            ratio = max_width / float(image.width)
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.LANCZOS)
        image.save(file_path, format="WEBP", quality=85)
        os.remove(temp_path)
        return f"/uploads/{new_filename}"
    except Exception as e:
        current_app.logger.error(f"Fel vid bildbehandling: {e}")
        flash("Ett fel uppstod när bilden skulle hanteras.", "warning")
        return ""

def send_new_post_notification(post):
    subscribers = User.query.filter_by(role='subscriber').all()
    for subscriber in subscribers:
        msg = Message(
            subject=f"Nytt blogginlägg: {post.title}",
            recipients=[subscriber.email],
            body=f"Ett nytt blogginlägg har publicerats: {post.title}\n\nLäs mer här: {url_for('blog.show_post', post_id=post.id, _external=True)}"
        )
        mail.send(msg)

@blog_bp.route("/")
@blog_bp.route("/page/<int:page>")
def index(page=1):
    POSTS_PER_PAGE = 12

    # Läs in GET-parametrar
    sort_order = request.args.get("sort", "desc")
    search_term = request.args.get("search", "").strip()
    category_filter = request.args.get("category", type=int)

    # Bas‐query: bara publicerade inlägg
    now = get_local_now()
    base_q = BlogPost.query.filter(BlogPost.created_at <= now)
    admin_q = BlogPost.query.order_by(BlogPost.created_at.desc())

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

    # 5) Applicera sök-filter om satt
    if search_term:
        base_q = base_q.filter(
            db.or_(
                BlogPost.title.ilike(f"%{search_term}%"),
                BlogPost.subtitle.ilike(f"%{search_term}%"),
                BlogPost.body.ilike(f"%{search_term}%"),
            )
        )

    # 6) Sortera
    order_func = BlogPost.created_at.asc() if sort_order == "asc" else BlogPost.created_at.desc()
    base_q = base_q.order_by(order_func)

    # 7) Paginerings‐logik
    total_posts = base_q.count()
    posts = (base_q
             .offset((page - 1) * POSTS_PER_PAGE)
             .limit(POSTS_PER_PAGE)
             .all())
    total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE

    # 8) Radera‐form
    delete_form = DeleteForm()

    # 9) Rendera templaten
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

@blog_bp.route("/category_images/<string:category_images>")
@blog_bp.route("/category_images/<string:category_images>/page/<int:page>")
def posts_by_category(category, page=1):
    sort_order = request.args.get('sort', 'desc')  # Default till 'desc' = nyast först
    query = BlogPost.query.filter_by(category=category)
    query = query.order_by(BlogPost.created_at.asc() if sort_order == 'oldest' else BlogPost.created_at.desc())

    total_posts = query.count()
    start = (page - 1) * POSTS_PER_PAGE
    posts = query.slice(start, start + POSTS_PER_PAGE).all()
    total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE

    return render_template("blog/layout.html", posts=posts, category=category,
                           page=page, total_pages=total_pages, sort_order=sort_order)


@blog_bp.route("/new_post", methods=["GET", "POST"])
@login_required
@admin_only
def new_post():
    form = BlogPostForm()
    cats = BlogCategory.query.order_by(BlogCategory.title).all()
    form.category.choices = [(c.id, c.title) for c in cats]

    if form.validate_on_submit():
        # --- Bildhantering ---
        img_url = "assets/img/default.jpg"
        if form.img_file.data:
            try:
                filename = save_image(form.img_file.data, folder="uploads/blog")
                img_url = f"uploads/blog/{filename}"
                print(f"Bild sparad som webp: {img_url}")
            except Exception as e:
                current_app.logger.error(f"Fel vid bildhantering: {e}")
                flash("Ett fel uppstod vid bildhantering. Använder standardbild.", "warning")

        # --- Datum- och tidslogik ---
        selected_date = form.date.data  # datetime.date
        selected_time_str = form.time.data  # t.ex. "21:21"

        try:
            parsed_time = datetime.strptime(selected_time_str, '%H:%M').time()
        except ValueError:
            flash("Ogiltigt tidsformat. Använd HH:MM.", "danger")
            return render_template("blog/new_post.html", form=form)

        # Kombinera till en naiv datetime (utan tidszon)
        naive_local_dt = datetime.combine(selected_date, parsed_time)

        # Lokaliserad till Europe/Stockholm
        local_tz = pytz.timezone("Europe/Stockholm")
        post_created_at_local = local_tz.localize(naive_local_dt)

        # Konvertera till UTC
        post_created_at_utc = post_created_at_local.astimezone(pytz.utc)

        print("Created at (local):", post_created_at_local.isoformat())
        print("Created at (UTC):", post_created_at_utc.isoformat())

        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=sanitize_html(form.body.data),
            created_at=post_created_at_utc,
            updated_at=None,
            img_url=img_url,
            category_id=form.category.data,
            author=current_user
        )

        try:
            db.session.add(new_post)
            db.session.commit()
            notify_subscribers(new_post)
            flash("Nytt inlägg har publicerats.", "success")
            return redirect(url_for("blog.index"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Fel vid databasoperation: {e}")
            flash("Ett fel uppstod när inlägget skulle sparas.", "danger")

    return render_template("blog/new_post.html", form=form)

@blog_bp.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    now = datetime.now(pytz.UTC)

    # Tvinga både created_at och updated_at att vara offset-aware (UTC)
    if post.created_at and post.created_at.tzinfo is None:
        post.created_at = post.created_at.replace(tzinfo=timezone.utc)

    if post.updated_at and post.updated_at.tzinfo is None:
        post.updated_at = post.updated_at.replace(tzinfo=timezone.utc)

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

    comment_form = CommentForm()
    delete_form = DeleteForm()

    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            abort(401)
        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=post
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


@blog_bp.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
@login_required
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)

    from app.utils.time import DEFAULT_TZ, get_local_now

    local_created_at = post.created_at.astimezone(DEFAULT_TZ)
    form = BlogPostForm(
        obj=post,
        date=local_created_at.date(),
        time=local_created_at.strftime('%H:%M')
    )

    cats = BlogCategory.query.order_by(BlogCategory.title).all()
    form.category.choices = [(c.id, c.title) for c in cats]

    if form.validate_on_submit():
        # --- Bildradering ---
        if form.delete_image.data and post.img_url and post.img_url != "assets/img/default.jpg":
            try:
                delete_existing_image(post.img_url, folder="")
            except Exception as e:
                current_app.logger.error(f"Fel vid radering av bild: {e}")
                flash("Kunde inte ta bort bilden.", "warning")
            post.img_url = "assets/img/default.jpg"

        # --- Ny bild ---
        if form.img_file.data:
            try:
                delete_existing_image(post.img_url, folder="")
                filename = save_image(form.img_file.data, folder="uploads/blog")
                post.img_url = f"uploads/blog/{filename}"
            except Exception as e:
                current_app.logger.error(f"Fel vid ny bilduppladdning: {e}")
                flash("Fel vid bilduppladdning.", "warning")

        # --- Text och metadata ---
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.body = sanitize_html(form.body.data)
        post.category_id = form.category.data

        # Om något ändrats: sätt updated_at
        if db.session.is_modified(post):
            post.updated_at = get_local_now().astimezone(timezone.utc)

        try:
            db.session.commit()
            flash("Inlägget har uppdaterats.", "success")
            return redirect(url_for("blog.show_post", post_id=post.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Fel vid uppdatering: {e}")
            flash("Fel vid sparning. Kontrollera loggarna.", "danger")

    return render_template("blog/edit_blog.html", form=form, post=post)
    

@blog_bp.route('/delete/<int:post_id>', methods=['POST'])
@login_required
@admin_only
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)

    if current_user.role != "admin":
        abort(403)

    db.session.delete(post)
    db.session.commit()
    flash("Inlägget raderades.", "info")
    return redirect(url_for("blog.index"))


@blog_bp.route('/upload', methods=['POST'])
@login_required
@admin_only
@csrf.exempt
def upload_image():
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
