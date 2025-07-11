# main.py

from app import create_app
from dotenv import load_dotenv
import os

# 🌱 Ladda miljövariabler från .env
load_dotenv()

app = create_app()

# ✅ Kontrollera om DATABASE_URL saknas i produktion
if app.config["FLASK_ENV"] == "production" and not app.config.get("SQLALCHEMY_DATABASE_URI"):
    raise RuntimeError("❌ DATABASE_URL saknas i produktionsmiljö!")

if __name__ == '__main__':
    app.run(debug=True)

