# MajaTingWorks 🌟

A professional portfolio, blog, and CV site built with Flask and MySQL — now GitHub Pages–friendly!
Swedish frontend, localization to-do.

---

## 🚀 Features

- **Blog** – create, edit, and publish posts using the Quill rich text editor.
- **Comments** – authenticated users can leave comments.
- **Portfolio & CV** – showcase your projects, skills, and experience.
- **User Roles & Auth** – admin, user, subscriber roles using Flask-Login.
- **CaptchaFox** – protect contact form with bot prevention.
- **Image Conversion** – auto converts uploads to WebP via Pillow.
- **Email Notifications** – notify subscribers of new posts.
- **MySQL + Migrations** – powered by Flask-Migrate.

---

## 📂 Project Structure

```
MajaTingWorks/
├── .venv/                 ← Virtual environment
├── app/
│   ├── admin/             ← Admin views and logic
│   ├── auth/              ← Login and password management
│   ├── blog/              ← Blog logic and utilities
│   ├── pages/             ← Static pages: home, contact, CV
│   ├── portfolio/         ← Portfolio section
│   ├── forms/             ← WTForms definitions
│   ├── utils/             ← Helpers: images, sanitize, notifications
│   ├── models.py          ← SQLAlchemy models
│   ├── decorators.py      ← Custom decorators (e.g., admin_only)
│   ├── extensions.py      ← Init for db, mail, login, csrf
│   └── __init__.py        ← App factory and blueprint registration
├── migrations/            ← Database migrations
├── static/                ← CSS, JS, images
├── templates/             ← Jinja2 templates
├── tools/                 ← Dev scripts and helpers
├── config.py              ← App config
├── main.py                ← App entrypoint / CLI
├── requirements.txt       ← Dependencies
└── README.md              ← This file
```

---

## ⚙️ Installation & Running

### 🧬 Create & Activate Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate     # macOS/Linux
.venv\Scripts\activate      # Windows
```

### 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

### 🔐 Configure Environment Variables

Create a `.env` file in your root directory:

```ini
DATABASE_URL=mysql+pymysql://<user>:<password>@<host>:3306/<dbname>
SECRET_KEY=your-super-secret
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your@email.com
MAIL_PASSWORD=yourpassword
MAIL_DEFAULT_SENDER=your@email.com
CAPTCHAFOX_SITE_KEY=sk_...
CAPTCHAFOX_SECRET_KEY=ok_...
```

### 🧱 Initialize Database

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### ▶️ Run the App

```bash
flask run
```

Visit [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🧪 Usage Overview

| Route               | Description                    |
|--------------------|--------------------------------|
| `/blog/`           | View blog posts                |
| `/blog/new_post`   | Create new post (admin only)   |
| `/blog/post/<id>`  | View specific post             |
| `/cv`              | CV section                     |
| `/portfolio`       | Portfolio section              |
| `/admin/`          | Admin panel                    |

---

## 🔧 Technologies

- **Python 3.11+**
- **Flask** with:
  - Flask-WTF
  - Flask-Login
  - Flask-Migrate
  - Flask-Mail
  - Flask-Bootstrap
  - Flask-CaptchaFox
  - Flask-Babel
- **SQLAlchemy** + MySQL (PyMySQL)
- **Pillow** for image handling
- **itsdangerous** for secure token workflows
- **GitHub Pages–friendly** layout

---
## Development Tools
### 🧹 Clean the project (Windows only)

The `tools/clean-project.ps1` script removes temporary files, for example:

- Python cache files (`*.pyc`, `__pycache__`)
- Swap/backup files (`*.bak`, `*~`, etc.)
- Unused `migrations/` folders (without `versions/`)
- Test or temporary images (`test`, `temp`, `debug` in `static/`)

... and then logs the results in a timestamped log file (e.g. tools/clean_log_2025-07-07_1340.txt)

To run the script (in PowerShell):

```powershell
./tools/clean-project.ps1
```

### 📄 `tools/generate_docs.py`

A helpful script that generates documentation and guide files for common Flask tasks. It creates a `docs/` directory (if not present) and fills it with `.txt` and optionally `.md` files containing quick reference tips and example code for topics like:

- CSRF troubleshooting
- Flask-Mail setup
- Pagination with SQLAlchemy
- Image upload handling
- User management
- Testing and debugging
- Deployment best practices

#### ✅ Usage:
```bash
python tools/generate_docs.py
```

### 🧩 `tools/inspect_models.py`

A developer utility that prints an overview of your SQLAlchemy models: all database tables and their columns. Useful for verifying schema structure or troubleshooting migrations.

#### ✅ Usage
```bash
python tools/inspect_models.py
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 🗒️ To-do

1. Unsubscribe as user / subscriber
2. Localize

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Feel free to reach out if you have any questions or suggestions!
