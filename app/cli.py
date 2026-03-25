# app/cli.py
import click
from flask.cli import with_appcontext
from app.blog.utils import check_and_send_blog_emails
from app.extensions import db
from app.models import User, Role
from werkzeug.security import generate_password_hash
from datetime import timezone

# ===================================================
# ✅ CLI-KOMMANDON
# ===================================================

@click.command('reset-stats')
@with_appcontext
def reset_stats():
    """
    Nollställ all visningsstatistik.
    
    ✅ Användning:
        flask reset-stats
    """
    from app.models import BlogPost, PageView
    
    # Nollställ blogginlägg
    for post in BlogPost.query.all():
        post.views = 0
    
    # Ta bort alla sidvisningar
    PageView.query.delete()
    
    db.session.commit()
    print("✅ All statistik nollställd!")


@click.command('aggregate-stats')
@click.option('--date', help='Datum att aggregera (YYYY-MM-DD). Default: igår')
@with_appcontext
def aggregate_stats(date):
    """
    Aggregera statistik för ett specifikt datum.
    
    ✅ Användning:
        flask aggregate-stats                    # Aggregera igår
        flask aggregate-stats --date 2026-03-24  # Specifikt datum
    
    ✅ Kör dagligen via cron:
        0 1 * * * cd /path/to/app && flask aggregate-stats
    """
    from app.models import BlogPost, PageView, DailyStats
    from datetime import date as date_class, timedelta
    
    # Bestäm vilket datum vi ska aggregera
    if date:
        target_date = date_class.fromisoformat(date)
    else:
        target_date = date_class.today() - timedelta(days=1)  # Igår
    
    print(f"📊 Aggregerar statistik för {target_date}...")
    
    # Hämta tidigare dagens statistik (om den finns)
    prev_date = target_date - timedelta(days=1)
    prev_stats = {s.page: s.views for s in DailyStats.query.filter_by(date=prev_date).all()}
    
    stats_to_save = []
    
    # 1. Blogginlägg
    for post in BlogPost.query.all():
        page_key = f"post_{post.id}"
        prev_views = prev_stats.get(page_key, 0)
        daily_views = max(0, post.views - prev_views)  # Skillnad sedan igår
        
        if daily_views > 0:
            stats_to_save.append(DailyStats(
                date=target_date,
                page=page_key,
                views=daily_views
            ))
    
    # 2. Vanliga sidor och portfolio
    for page_view in PageView.query.all():
        prev_views = prev_stats.get(page_view.page, 0)
        daily_views = max(0, page_view.views - prev_views)
        
        if daily_views > 0:
            stats_to_save.append(DailyStats(
                date=target_date,
                page=page_view.page,
                views=daily_views
            ))
    
    # Spara allt på en gång
    if stats_to_save:
        db.session.bulk_save_objects(stats_to_save)
        db.session.commit()
        print(f"✅ Sparade {len(stats_to_save)} poster för {target_date}")
    else:
        print(f"ℹ️  Inga nya visningar för {target_date}")


@click.command('create-admin')
@click.option('--email', prompt='Email', help='Admin email')
@click.option('--name', prompt='Namn', default='Admin', help='Admin namn')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Lösenord')
@with_appcontext
def create_admin(email, name, password):
    """
    Skapa admin-användare och nödvändiga roller.
    
    ✅ Användning:
        flask create-admin
        
    ✅ Med argument:
        flask create-admin --email admin@example.com --name Admin --password MittLösenord
    """
    
    # 1. Skapa roller om de inte finns
    print("\n📋 Skapar roller...")
    roles_to_create = ['admin', 'user', 'subscriber']
    
    for role_name in roles_to_create:
        existing_role = Role.query.filter_by(name=role_name).first()
        if not existing_role:
            role = Role(name=role_name)
            db.session.add(role)
            print(f"  ✅ Skapade roll: {role_name}")
        else:
            print(f"  ℹ️  Roll finns redan: {role_name}")
    
    db.session.commit()
    
    # 2. Kolla om användaren redan finns
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        print(f"\n❌ Användare med email '{email}' finns redan!")
        return
    
    # 3. Skapa admin-användare
    print(f"\n👤 Skapar admin-användare...")
    admin = User(
        email=email,
        name=name,
        password=generate_password_hash(password, method='pbkdf2:sha256')
    )
    
    # 4. Lägg till roller
    admin.add_role('admin')
    admin.add_role('user')
    
    db.session.add(admin)
    db.session.commit()
    
    # 5. Bekräftelse
    print(f"\n✅ Admin-konto skapat!")
    print(f"   📧 Email: {admin.email}")
    print(f"   👤 Namn: {admin.name}")
    print(f"   🔑 Roller: {', '.join([r.name for r in admin.roles])}")
    print(f"\n🚀 Logga in på: http://localhost:5000/login\n")