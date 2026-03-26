#!/usr/bin/env python3
"""
Backup-script för blogginlägg från MajaTingWorks
Exporterar alla inlägg till JSON-format för enkel import senare
"""

import json
import sys
from datetime import datetime

# Lägg till app-rooten i sys.path så vi kan importera
sys.path.insert(0, '/path/to/MajaTingWorks')  # ← ÄNDRA TILL DIN SÖKVÄG

from app import create_app, db
from app.models import BlogPost, BlogCategory, User

def backup_blog_posts():
    """Exportera alla blogginlägg till JSON"""
    app = create_app()
    
    with app.app_context():
        posts = BlogPost.query.all()
        
        backup_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "total_posts": len(posts),
            "posts": []
        }
        
        for post in posts:
            post_data = {
                "id": post.id,
                "title": post.title,
                "subtitle": post.subtitle,
                "body": post.body,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "updated_at": post.updated_at.isoformat() if post.updated_at else None,
                "img_url": post.img_url,
                "views": post.views or 0,
                "author_email": post.author.email if post.author else None,
                "author_name": post.author.name if post.author else None,
                "category_name": post.category.name if post.category else None,
                "category_title": post.category.title if post.category else None,
            }
            backup_data["posts"].append(post_data)
        
        # Spara till fil med timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"blog_backup_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Backup klar!")
        print(f"   📁 Fil: {filename}")
        print(f"   📝 Antal inlägg: {len(posts)}")
        print(f"\n🔍 Första 3 inlägg:")
        for i, post in enumerate(posts[:3], 1):
            print(f"   {i}. {post.title} ({post.created_at})")

if __name__ == "__main__":
    backup_blog_posts()
