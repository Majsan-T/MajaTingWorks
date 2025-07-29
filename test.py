# test.py
import os
from dotenv import load_dotenv

load_dotenv()  # 🔑 Ladda .env med t.ex. SQLALCHEMY_DATABASE_URI

from app import create_app
from app.extensions import db
from app.models import User, Role

app = create_app()

with app.app_context():
    print("🔗 Ansluter till:", app.config.get("SQLALCHEMY_DATABASE_URI"))

    # Hämta alla adminanvändare
    admins = User.query.join(User.roles).filter(Role.name == "admin").all()
    for admin in admins:
        print(f"👑 {admin.name} ({admin.email}) är admin")
