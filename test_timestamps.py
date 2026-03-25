# tests/test_timestamps.py
"""
Enhetstester för tidsstämpelhantering.

Kör:
    pytest tests/test_timestamps.py
    
Kör med coverage:
    pytest --cov=app.utils.time tests/test_timestamps.py
"""

import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def test_get_local_now_returns_utc():
    """
    Verifiera att get_local_now() returnerar UTC-tid.
    
    Detta är viktigt eftersom vi ALLTID ska spara i UTC i databasen.
    """
    from app.utils.time import get_local_now
    
    now = get_local_now()
    
    # Ska returnera en datetime
    assert isinstance(now, datetime)
    
    # Ska ha tidszon
    assert now.tzinfo is not None
    
    # Ska vara UTC
    assert now.tzinfo == ZoneInfo("UTC")


def test_get_display_time_converts_to_stockholm():
    """
    Verifiera att get_display_time() konverterar UTC till Stockholm-tid.
    """
    from app.utils.time import get_display_time
    
    # Skapa en UTC-tid: 12:00 UTC
    utc_time = datetime(2025, 3, 24, 12, 0, tzinfo=ZoneInfo("UTC"))
    
    # Konvertera till visning
    display_time = get_display_time(utc_time)
    
    # Ska vara Stockholm-tid
    assert display_time.tzinfo == ZoneInfo("Europe/Stockholm")
    
    # I mars är det vintertid (UTC+1), så 12:00 UTC = 13:00 Stockholm
    # OBS: Detta kan vara UTC+2 under sommartid!
    assert display_time.hour in [13, 14]  # Beroende på sommartid


def test_get_display_time_handles_naive_datetime():
    """
    Verifiera att naive datetime behandlas som UTC.
    """
    from app.utils.time import get_display_time
    
    # Skapa en naive datetime (utan tidszon)
    naive_dt = datetime(2025, 3, 24, 12, 0)
    
    # Ska tolkas som UTC och konverteras till Stockholm
    display_time = get_display_time(naive_dt)
    
    # Ska ha Stockholm-tidszon
    assert display_time.tzinfo == ZoneInfo("Europe/Stockholm")


def test_parse_form_datetime_winter():
    """
    Testa konvertering från formulär till UTC under vintertid.
    """
    from app.utils.time import parse_form_datetime
    
    # Stockholm vintertid: 24 mars 2025, 14:30
    # Detta ska bli 13:30 UTC (UTC+1)
    utc_dt = parse_form_datetime('2025-03-24', '14:30')
    
    # Ska vara UTC
    assert utc_dt.tzinfo == ZoneInfo("UTC")
    
    # 14:30 Stockholm = 13:30 UTC i mars (vintertid)
    assert utc_dt.hour == 13
    assert utc_dt.minute == 30


def test_parse_form_datetime_summer():
    """
    Testa konvertering från formulär till UTC under sommartid.
    """
    from app.utils.time import parse_form_datetime
    
    # Stockholm sommartid: 24 juli 2025, 14:30
    # Detta ska bli 12:30 UTC (UTC+2)
    utc_dt = parse_form_datetime('2025-07-24', '14:30')
    
    # Ska vara UTC
    assert utc_dt.tzinfo == ZoneInfo("UTC")
    
    # 14:30 Stockholm = 12:30 UTC i juli (sommartid)
    assert utc_dt.hour == 12
    assert utc_dt.minute == 30


def test_parse_form_datetime_invalid_date():
    """
    Verifiera att ogiltig datumformat kastar ValueError.
    """
    from app.utils.time import parse_form_datetime
    
    with pytest.raises(ValueError):
        parse_form_datetime('2025-13-45', '14:30')  # Ogiltigt datum


def test_parse_form_datetime_invalid_time():
    """
    Verifiera att ogiltig tidsformat kastar ValueError.
    """
    from app.utils.time import parse_form_datetime
    
    with pytest.raises(ValueError):
        parse_form_datetime('2025-03-24', '25:70')  # Ogiltig tid


def test_roundtrip_conversion():
    """
    Testa att vi kan konvertera fram och tillbaka utan att förlora data.
    
    Stockholm → UTC → Stockholm ska ge samma tid.
    """
    from app.utils.time import parse_form_datetime, get_display_time
    
    # Start: 24 mars 2025, 14:30 i Stockholm
    original_date = '2025-03-24'
    original_time = '14:30'
    
    # Konvertera till UTC (för databas)
    utc_dt = parse_form_datetime(original_date, original_time)
    
    # Konvertera tillbaka till Stockholm (för visning)
    display_dt = get_display_time(utc_dt)
    
    # Ska vara samma tid
    assert display_dt.hour == 14
    assert display_dt.minute == 30
    assert display_dt.day == 24
    assert display_dt.month == 3
    assert display_dt.year == 2025


# Integrationstester med Flask-appen
@pytest.fixture
def app():
    """Skapa en testapp."""
    import os
    from app import create_app
    
    # Sätt DATABASE_URI före create_app anropas
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['TESTING'] = 'True'
    
    app = create_app()
    
    with app.app_context():
        from app.extensions import db
        db.create_all()
        yield app
        db.drop_all()
    
    # Rensa miljövariabler efter testet
    os.environ.pop('DATABASE_URL', None)
    os.environ.pop('TESTING', None)


@pytest.fixture
def client(app):
    """Skapa en test-klient."""
    return app.test_client()


def test_blog_post_saves_in_utc(app):
    """
    Integrations-test: Verifiera att blogginlägg sparas i UTC.
    """
    from app.models import BlogPost, User, BlogCategory
    from app.extensions import db
    from app.utils.time import get_local_now
    
    with app.app_context():
        # Skapa testdata
        category = BlogCategory(name='test', title='Test')
        db.session.add(category)
        
        user = User(email='test@test.com', name='Test', password='test123')
        db.session.add(user)
        db.session.commit()
        
        # Skapa blogginlägg
        post = BlogPost(
            title='Test',
            subtitle='Test',
            body='Test',
            img_url='test.jpg',
            created_at=get_local_now(),
            category_id=category.id,
            author_id=user.id
        )
        db.session.add(post)
        db.session.commit()
        
        # Hämta från databas
        saved_post = BlogPost.query.first()
        
        # Ska ha tidszon
        assert saved_post.created_at.tzinfo is not None
        
        # Ska vara UTC
        assert saved_post.created_at.tzinfo == ZoneInfo("UTC")


def test_blog_post_displays_in_stockholm(app):
    """
    Integrations-test: Verifiera att tid visas i Stockholm-tid i templates.
    """
    from app.models import BlogPost, User, BlogCategory
    from app.extensions import db
    from app.utils.time import get_local_now, get_display_time
    from datetime import datetime
    
    with app.app_context():
        # Skapa testdata
        category = BlogCategory(name='test', title='Test')
        db.session.add(category)
        
        user = User(email='test@test.com', name='Test', password='test123')
        db.session.add(user)
        db.session.commit()
        
        # Skapa blogginlägg med känd UTC-tid
        utc_time = datetime(2025, 3, 24, 12, 0, tzinfo=ZoneInfo("UTC"))
        post = BlogPost(
            title='Test',
            subtitle='Test',
            body='Test',
            img_url='test.jpg',
            created_at=utc_time,
            category_id=category.id,
            author_id=user.id
        )
        db.session.add(post)
        db.session.commit()
        
        # Hämta och konvertera till visning
        saved_post = BlogPost.query.first()
        display_time = get_display_time(saved_post.created_at)
        
        # Ska vara 13:00 i Stockholm (UTC+1 i mars)
        assert display_time.hour == 13


# Testa Jinja-filter
def test_format_datetime_sv_filter(app):
    """
    Test av Jinja-filtret för svensk datumformattering.
    """
    from app.utils.filters import format_datetime_sv
    from datetime import datetime
    
    with app.app_context():
        # Skapa en UTC-tid
        utc_time = datetime(2025, 3, 24, 12, 0, tzinfo=ZoneInfo("UTC"))
        
        # Formatera
        formatted = format_datetime_sv(utc_time)
        
        # Ska innehålla svenskt datumformat
        assert 'mars' in formatted.lower()
        assert '2025' in formatted
        
        # Ska visa Stockholm-tid (13:00)
        assert '13:00' in formatted


if __name__ == '__main__':
    pytest.main([__file__, '-v'])