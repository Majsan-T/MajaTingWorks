# tools/generate_docs.py
from pathlib import Path
import os

# === Skapa docs-mapp och undermappar ===
docs_path = Path("docs")
docs_path.mkdir(exist_ok=True)
md_path = docs_path / "Markdown"
md_path.mkdir(exist_ok=True)

# === Guider som markdown och text ===
guides = {
    "CSRF-Troubleshooting.txt": """\n\U0001f6e1️ CSRF-FELS\u00d6KNING I FLASK\n\nProblem:\n--------\n\"\u26d4 CSRF token is missing.\"\n\nL\u00f6sningar:\n----------\n\n1. Kontrollera att du anv\u00e4nder Flask-WTF:\n------------------------------------------\nfrom flask_wtf import FlaskForm\n\n2. I din layout/base.html – inkludera csrf_token:\n-------------------------------------------------\n{{ form.hidden_tag() }}\n\n3. Kontrollera att du anv\u00e4nder `form = YourForm()` i vyn.\n\n4. L\u00e4gg till SECRET_KEY i __init__.py:\n--------------------------------------\napp.config['SECRET_KEY'] = os.getenv(\"SECRET_KEY\")\n\n5. Om du inte anv\u00e4nder FlaskForm:\n---------------------------------\nAnv\u00e4nd `@csrf.exempt` p\u00e5 din vy, men BARA om det \u00e4r s\u00e4kert.\n\n6. HTML-formul\u00e4r:\n-----------------\nSe till att du anv\u00e4nder en POST-metod och inte GET.\n\nTips:\n-----\n- Om du inte har <form method=\"POST\"> f\u00e5r du alltid CSRF-fel.\n""",
    "Email-Setup-Guide.txt": """\n\U0001f4e7 E-POSTKONFIGURATION F\u00d6R FLASK\n\n1. .env-filen (l\u00e4gg till och h\u00e5ll hemlig):\n----------------------------------------\nMAIL_USERNAME=\"din@mail.se\"\nMAIL_PASSWORD=\"app-l\u00f6senord\"\nMAIL_DEFAULT_SENDER=\"din@mail.se\"\n\n2. __init__.py – l\u00e4gg till i app.config:\n----------------------------------------\napp.config['MAIL_SERVER'] = 'smtp.gmail.com'\napp.config['MAIL_PORT'] = 587\napp.config['MAIL_USE_TLS'] = True\napp.config['MAIL_USERNAME'] = os.getenv(\"MAIL_USERNAME\")\napp.config['MAIL_PASSWORD'] = os.getenv(\"MAIL_PASSWORD\")\napp.config['MAIL_DEFAULT_SENDER'] = os.getenv(\"MAIL_DEFAULT_SENDER\")\n\n3. Inkludera mail:\n------------------\nfrom flask_mail import Mail, Message\nmail = Mail()\nmail.init_app(app)\n\n4. Skicka mejl (t.ex. i notify_subscribers):\n-------------------------------------------\nmsg = Message(subject=\"Nyhet\",\n              sender=app.config['MAIL_DEFAULT_SENDER'],\n              recipients=[\"exempel@doman.se\"])\nmsg.body = \"Hej!\"\nmail.send(msg)\n"""
}

# === Spara .txt-guider ===
for filename, content in guides.items():
    with open(docs_path / filename, "w", encoding="utf-8") as f:
        f.write(content)

# === Spara .md-version av CSRF-guide ===
csrf_md = guides.get("CSRF-Troubleshooting.txt")
if csrf_md:
    with open(md_path / "CSRF-Troubleshooting.md", "w", encoding="utf-8") as f:
        f.write("# \U0001f6e1️ CSRF Troubleshooting\n\n" + csrf_md)

# === Lista alla skapade filer ===
print("F\u00f6ljande guider har skapats i /docs:")
for path in sorted(docs_path.glob("*.txt")):
    print(" •", path.name)

print("\nMarkdown-filer:")
for path in sorted(md_path.glob("*.md")):
    print(" •", path.name)
