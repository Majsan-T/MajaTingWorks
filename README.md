# MajaTingWorks 🌟

A professional portfolio, blog, and CV site built with Flask and MySQL — now GitHub Pages–friendly!

---

## 🚀 Features

- **Blog** – Create, edit, and publish posts using the Quill rich text editor.
- **Comments** – Authenticated users can leave comments.
- **Portfolio & CV** – Showcase your projects, skills, and experience.
- **User Roles & Auth** – Admin, user, subscriber roles using Flask-Login.
- **CaptchaFox** – Protect the contact form with bot prevention.
- **Image Conversion** – Automatically converts uploaded images to WebP using Pillow.
- **Email Notifications** – Notifies subscribers when a new blog post is published.
- **MySQL + Migrations** – Powered by Flask-Migrate.

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
.venv\Scripts\activate        # Windows
```

### 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

### 🔐 Configure Environment Variables

Create a `.env` file in your project root:

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

| Route              | Description                  |
|--------------------|------------------------------|
| `/blog/`           | View blog posts              |
| `/blog/new_post`   | Create new post (admin only) |
| `/blog/post/<id>`  | View specific post           |
| `/cv`              | CV section                   |
| `/portfolio`       | Portfolio section            |
| `/admin/`          | Admin panel                  |

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

## ✉️ Mailutskick & GDPR-anpassad Kontohantering

### 🔐 GDPR & Anonymisering av konton

- **Anonymisering:**  
  När en användare raderas eller ett konto inaktiveras permanent anonymiseras det enligt GDPR.  
  - Originalmailen ersätts med en dummyadress:  
    `deleted_user_<id>@example.com`  
  - Namn ersätts med `"Raderad användare"`.  
  - Fältet `is_deleted=True` sätts och `is_active` låses till `False`.  
  - Alla blogginlägg och kommentarer kopplade till kontot anonymiseras eller raderas beroende på systeminställningar.

- **Ej återställbart:**  
  Anonymisering är **permanent** – användaren kan inte återaktiveras eftersom originaladressen är borta.

- **Adminpanel:**  
  Admins kan se anonymiserade konton markerade med en grå rad och texten *Inaktiv* i användarlistan.  
  En "Aktivera"-knapp visas **inte** för anonymiserade konton.

- **Dummy-domäner:**  
  Dummyadresser använder reserverade domäner (`example.com`) enligt [RFC 2606](https://datatracker.ietf.org/doc/html/rfc2606), vilket gör dem säkra och ej routade.

---

### ✉️ Mailutskick & Hantering av prenumeranter

- **Notifieringar:**  
  - Prenumeranter får automatiska mail när nya blogginlägg publiceras.  
  - Utskicket sker via kommandot `flask send-blog-mails` eller automatiskt via cron-jobb.

- **Inaktiverade konton & mail:**  
  - Systemet skickar **aldrig** mail till konton där `is_active=False` eller e-postadressen slutar på:  
    - `example.com`  
    - `example.net`  
    - `example.org`  
    - `invalid`  
  - En intern funktion (`is_dummy_email()`) blockerar alla utskick till anonymiserade konton.

- **Avsluta prenumeration:**  
  Prenumeranter kan själva avregistrera sig via länk i e-postutskick.  
  Admin kan också inaktivera prenumeranter via adminpanelen.

---

## 🚜 CLI Commands

### ✉️ `send-blog-mails`

Sends email notifications to subscribers when a blog post's `created_at` timestamp has passed and the post hasn't been emailed yet.

#### ✅ Usage:

```bash
flask send-blog-mails
```

> Each post is marked as sent by setting `email_sent = True`.

---

## 📆 Cron Jobs

Want to send blog emails automatically every day? Add the following to your crontab to run the command at 9:00 PM daily:

```cron
0 21 * * * cd /home/your/path/to/root-folder && FLASK_APP=main.py FLASK_CLI=true flask send-blog-mails >> logs/send_blog_mails.log 2>&1
```

📌 **Prerequisites:**

- Flask CLI must work in your environment.
- A `logs/` directory should exist in the project root.
- Environment variables must be accessible via `.env` or system config.

> Edit your crontab with `crontab -e`.  
> In `vim`, press `Esc`, type `:wq`, then press Enter to save and exit.

---

## Development Tools

### 🧹 Clean the Project (Windows Only)

The `tools/clean-project.ps1` script removes temporary files such as:

- Python cache files (`*.pyc`, `__pycache__`)
- Swap/backup files (`*.bak`, `*~`, etc.)
- Unused `migrations/` folders (without `versions/`)
- Test or temporary images (`test`, `temp`, `debug` in `static/`)

Creates a timestamped log file, e.g., `tools/clean_log_2025-07-07_1340.txt`

```powershell
./tools/clean-project.ps1
```

### 📄 `tools/generate_docs.py`

Generates docs and quick guides for common Flask tasks. Outputs `.txt` and `.md` files to a `docs/` directory.

```bash
python tools/generate_docs.py
```

### 🤩 `tools/inspect_models.py`

Prints all database tables and their columns. Helpful for checking schema consistency and debugging.

```bash
python tools/inspect_models.py
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to your branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 🗒️ To-do

1. Unsubscribe as user/subscriber – Done
2. Refine date/time handling for `posted_at` and `updated_at` – Done
3. Localization support

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Feel free to reach out if you have any questions or suggestions!
