# MajaTingWorks 🌟

En professionell portfolio, blogg och CV-sida byggd med Flask och MySQL — med GDPR-säker statistik och automatiska bloggmail!

---

## 🚀 Funktioner

- **Blogg** – Skapa, redigera och publicera inlägg med hjälp av den rika texteditorn Quill.
- **Schemalagda inlägg** – Publicera blogginlägg i framtiden, mail skickas automatiskt när inlägget går live.
- **Kommentarer** – Inloggade användare kan lämna kommentarer.
- **Portfolio & CV** – Visa upp projekt, färdigheter och erfarenheter.
- **Användarroller & Inloggning** – Roller för administratör, användare och prenumerant via Flask-Login.
- **GDPR-säker statistik** – Session-baserad visningsräkning med bot-filtering och historisk data.
- **Automatiska e-postnotifieringar** – APScheduler skickar mail till prenumeranter var 15:e minut (ingen cron behövs!).
- **CaptchaFox** – Skyddar kontaktformuläret mot botar.
- **Bildkonvertering** – Uppladdade bilder konverteras automatiskt till WebP med hjälp av Pillow.
- **MySQL + Migreringar** – Drivs av Flask-Migrate.

---

## 📂 Projektstruktur

```
MajaTingWorks/
├── .venv/                 ← Virtuell miljö
├── app/
│   ├── admin/             ← Adminvyer och logik
│   ├── auth/              ← Inloggning och lösenordshantering
│   ├── blog/              ← Blogglogik och hjälpverktyg
│   ├── pages/             ← Statiska sidor: startsida, kontakt, CV
│   ├── portfolio/         ← Portfoliosektion
│   ├── forms/             ← WTForms-formulär
│   ├── utils/             ← Hjälpfunktioner: bilder, sanering, notiser, statistik
│   ├── models.py          ← SQLAlchemy-modeller
│   ├── decorators.py      ← Dekoratorer (t.ex. roles_required)
│   ├── extensions.py      ← Initiering av db, mail, login, csrf
│   ├── scheduler.py       ← APScheduler för automatiska bloggmail
│   └── __init__.py        ← Appfabrik och blueprint-registrering
├── migrations/            ← Databasens migreringsmappar
├── static/                ← CSS, JS, bilder
│   ├── uploads/           ← Uppladdade bilder (blogg, portfolio)
│   ├── blog_category_images/
│   └── portfolio_category_images/
├── templates/             ← Jinja2-mallar
├── tools/                 ← Utvecklingsskript
├── config.py              ← Appkonfiguration
├── main.py                ← Startfil för appen / CLI
├── requirements.txt       ← Beroenden
├── README.md              ← Denna fil
└── backup_blog.py         ← Backup av bloggen
```

---

## ⚙️ Installation & Körning

### 🧬 Skapa och aktivera virtuell miljö

```bash
python3 -m venv .venv
source .venv/bin/activate     # macOS/Linux
.venv\Scripts\activate        # Windows
```

### 📦 Installera beroenden

```bash
pip install -r requirements.txt
```

**Viktiga beroenden:**
- Flask 3.0+
- SQLAlchemy
- Flask-Migrate
- Flask-Mail
- APScheduler 3.10+ (för automatiska bloggmail)
- Pillow (bildhantering)
- PyMySQL (MySQL-koppling)

### 🔐 Konfigurera miljövariabler

Skapa en `.env`-fil i projektets rot:

```ini
DATABASE_URL=mysql+pymysql://<user>:<password>@<host>:3306/<dbname>
SECRET_KEY=your-super-secret-key-here
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your@email.com
MAIL_PASSWORD=yourpassword
MAIL_DEFAULT_SENDER=your@email.com
CAPTCHAFOX_SITE_KEY=sk_...
CAPTCHAFOX_SECRET_KEY=ok_...
```

### 🧱 Initiera databasen

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### ▶️ Starta appen

```bash
flask run
```

Besök [http://127.0.0.1:5000](http://127.0.0.1:5000)

När appen startar ska du se:
```
📧 Bloggmail-scheduler startad! Körs var 15:e minut.
```

---

## 🧪 Användningsöversikt

| Route             | Beskrivning                      |
| ----------------- | -------------------------------- |
| `/`               | Startsida                        |
| `/blog/`          | Visa blogginlägg                 |
| `/blog/new_post`  | Skapa nytt inlägg (endast admin) |
| `/blog/post/<id>` | Visa specifikt inlägg            |
| `/cv`             | CV-sektion                       |
| `/contact`        | Kontaktformulär                  |
| `/portfolio`      | Portfolio-sektion                |
| `/admin/`         | Adminpanel (översikt)            |
| `/admin/views`    | Visningsstatistik                |

---

## 📊 GDPR-säker statistik

### ✅ Session-baserad visningsräkning
- **Ingen IP-spårning** – endast session cookies används
- **Bot-filtering** – Google Bot, Bing Bot m.fl. räknas inte
- **Unika visningar** – Max 1 visning per session per sida
- **Historisk data** – Daglig aggregering för trendanalys

### 📈 Databastabeller
- `page_views` – Kumulativa visningar per sida
- `daily_stats` – Daglig historik för statistikfilter
- `blog_posts.views` – Visningar per blogginlägg

### 🔧 Statistikfunktioner
- **Tidsfilter:** 7 dagar, 30 dagar, 90 dagar, Alla
- **Aggregering:** Automatisk via CLI-kommando `aggregate-stats`
- **Adminpanel:** `/admin/views` visar blogg, sidor och portfolio separat

---

## 📧 Automatiska bloggmail med APScheduler

### ⏰ Hur det fungerar
1. **Skapa inlägg** med framtida publiceringsdatum (t.ex. imorgon kl 17:00)
2. **Inlägget sparas** med `email_sent = False`
3. **APScheduler körs var 15:e minut** i bakgrunden
4. **När klockan blir 17:00** skickas mail automatiskt till prenumeranter
5. **`email_sent` sätts till True** – inget duplikatmail

### ✅ Fördelar
- **Ingen cron/cronjob behövs** – APScheduler körs inuti Flask-appen
- **Automatiskt vid omstart** – Schedulern startar när appen startar
- **Max 15 minuters delay** – Om inlägg publiceras kl 17:03 skickas mail senast 17:15

### 🔧 Inställningar
Schedulern startas automatiskt i `app/__init__.py`:
```python
from app.scheduler import start_scheduler
start_scheduler(app)
```

**Ändra intervall** (valfritt):
I `app/scheduler.py`, ändra:
```python
trigger=IntervalTrigger(minutes=15),  # ← Ändra till 5, 30, 60 etc.
```

### 📋 Mailutskick-logik
- **Max 10 blogginlägg** skickas per körning
- **Alla prenumeranter** får mail för varje inlägg
- **Manuell utskick:** Via knapp i adminpanelen eller `flask send-blog-mails`

---

## 🛠️ CLI-kommandon

### Bloggmail & Schemaläggning

#### `flask send-blog-mails`
Skickar mail manuellt (samma som schedulern kör automatiskt):
```bash
flask send-blog-mails
```

### Statistik & Data

#### `flask aggregate-stats`
Aggregerar visningsstatistik för en specifik dag:
```bash
flask aggregate-stats                    # Aggregerar igår
flask aggregate-stats --date 2026-03-24  # Aggregerar specifikt datum
```

**Rekommendation:** Kör automatiskt varje natt kl 01:00 via Task Scheduler (Windows) eller cron (Linux/Mac).

#### `flask reset-stats`
Återställer all statistik till 0 (använd med försiktighet!):
```bash
flask reset-stats
```

### Databasunderhåll

#### `flask fix-post-timestamps`
Fixar tidszoner för blogginlägg (lägger till UTC om saknas):
```bash
flask fix-post-timestamps
```

#### `flask reset-bad-updated-at`
Återställer felaktiga `updated_at`-datum (där `updated_at < created_at`):
```bash
flask reset-bad-updated-at
```

---

## 🔐 GDPR & Användarhantering

### ✅ Rollsystem
- **Admin** – Fullständig åtkomst till adminpanelen
- **User** – Kan kommentera blogginlägg
- **Subscriber** – Får mail när nya blogginlägg publiceras

### 🗑️ Anonymisering av konton (GDPR)
När en användare raderas anonymiseras kontot permanent:
- Email → `anonymized_<id>@example.com`
- Namn → `"Raderad användare"`
- `is_deleted = True`, `is_active = False`
- **Ej återställbart** – originaldata är borttagen

### 📧 Mailutskick & Dummy-adresser
Systemet skickar **aldrig** mail till:
- Anonymiserade konton (`anonymized_*@example.com`)
- Inaktiva konton (`is_active = False`)
- Dummy-domäner: `example.com`, `example.net`, `example.org`, `invalid`

---

## 🔧 Teknik

### Backend
- **Python 3.11+**
- **Flask 3.0+** med:
  - Flask-WTF (formulär + CSRF-skydd)
  - Flask-Login (autentisering)
  - Flask-Migrate (databasmigrering)
  - Flask-Mail (e-postutskick)
  - Flask-Babel (internationalisering)
- **SQLAlchemy** + MySQL (via PyMySQL)
- **APScheduler** (bakgrundsschemaläggning)
- **Pillow** (bildhantering & WebP-konvertering)
- **itsdangerous** (säkra tokens)

### Frontend
- **Bootstrap 5** (responsiv design)
- **Quill.js** (rich text editor)
- **Bootstrap Icons**
- **Custom CSS** för blogg och portfolio

### Säkerhet
- **CSRF-skydd** via Flask-WTF
- **CaptchaFox** (bot-skydd på kontaktformulär)
- **Rollbaserad åtkomstkontroll** (`@roles_required`)
- **Lösenordshasning** (Werkzeug PBKDF2)
- **Token-baserad lösenordsåterställning** (tidsbegränsade tokens)

---

## 🤝 Bidra till projektet

1. Forka detta repo  
2. Skapa en ny feature-branch: `git checkout -b feature/din-funktion`  
3. Lägg till dina ändringar: `git commit -m 'Lagt till ny funktion'`  
4. Skicka till ditt repo: `git push origin feature/din-funktion`  
5. Skapa en Pull Request

---

## 🗒️ Att göra

- [ ] Förbättrad bildgalleri för portfolio
- [ ] RSS-flöde för bloggen
- [ ] Sök-funktion i bloggen (fulltext search)
- [ ] Taggar för blogginlägg
- [ ] Export av statistik till CSV/Excel
- [ ] Dark mode
- [ ] Stöd för lokaliserad översättning (i18n/l10n)

**Klart:**
- [x] Avregistrera sig som användare/prenumerant
- [x] Förbättrad hantering av datum/tid för `created_at` och `updated_at`
- [x] GDPR-säker statistik med session-tracking och bot-filtering
- [x] Automatiska bloggmail med APScheduler (ingen cron behövs)
- [x] Daglig statistikaggregering med tidsfilter
- [x] Rollbaserat användarsystem med flera roller per användare

---

## 📄 Licens

Detta projekt är licensierat under MIT-licensen. Se [LICENSE](LICENSE) för mer information.

---

## 💡 Support & Kontakt

Hör gärna av dig om du har frågor eller förslag!

**Utvecklat med ❤️ av Maria Tingvall**