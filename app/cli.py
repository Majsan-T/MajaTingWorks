# app/cli.py
from flask.cli import with_appcontext
import click
from datetime import timezone
from app.models import BlogPost
from app.extensions import db
# from app.blog.cli import send_blog_mails

def register_cli_commands(app):
    # app.cli.add_command(send_blog_mails)
    pass

@click.command("fix-post-timestamps")
@with_appcontext
def fix_post_timestamps():
    """Gör alla created_at / updated_at fält offset-aware (UTC)."""
    fixed_count = 0
    posts = BlogPost.query.all()

    for post in posts:
        changed = False
        if post.created_at and post.created_at.tzinfo is None:
            post.created_at = post.created_at.replace(tzinfo=timezone.utc)
            changed = True

        if post.updated_at and post.updated_at.tzinfo is None:
            post.updated_at = post.updated_at.replace(tzinfo=timezone.utc)
            changed = True

        if changed:
            fixed_count += 1

    db.session.commit()
    click.echo(f"✅ {fixed_count} inlägg uppdaterades med UTC-tidszon.")



@click.command("reset-bad-updated-at")
@with_appcontext
def reset_bad_updated_at():
    """Sätter updated_at = None om det är tidigare än created_at."""
    fixed_count = 0
    posts = BlogPost.query.all()

    for post in posts:
        if post.updated_at and post.created_at:
            try:
                if post.updated_at < post.created_at:
                    click.echo(f"⚠️ Post ID {post.id}: updated_at ({post.updated_at}) < created_at ({post.created_at})")
                    post.updated_at = None
                    fixed_count += 1
            except TypeError:
                click.echo(f"❗ Post ID {post.id}: mismatch mellan offset-naiv och offset-aware datetime.")

    db.session.commit()
    click.echo(f"✅ {fixed_count} inlägg återställdes (updated_at satt till NULL).")