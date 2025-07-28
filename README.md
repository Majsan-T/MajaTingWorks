# MajaTingWorks 🌟

En professionell portfolio, blogg och CV-sida byggd med Flask och MySQL — nu kompatibel med GitHub Pages!

---

## 🚀 Funktioner

- **Blogg** – Skapa, redigera och publicera inlägg med hjälp av den rika texteditorn Quill.
- **Kommentarer** – Inloggade användare kan lämna kommentarer.
- **Portfolio & CV** – Visa upp projekt, färdigheter och erfarenheter.
- **Användarroller & Inloggning** – Roller för administratör, användare och prenumerant via Flask-Login.
- **CaptchaFox** – Skyddar kontaktformuläret mot botar.
- **Bildkonvertering** – Laddade bilder konverteras automatiskt till WebP med hjälp av Pillow.
- **E-postnotifieringar** – Skickar mail till prenumeranter när ett nytt blogginlägg publiceras.
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
│   ├── pages/             ← Statisk sidor: startsida, kontakt, CV
│   ├── portfolio/         ← Portfoliosektion
│   ├── forms/             ← WTForms-formulär
│   ├── utils/             ← Hjälpfunktioner: bilder, sanering, notiser
│   ├── models.py          ← SQLAlchemy-modeller
│   ├── decorators.py      ← Dekoratorer (t.ex. roles_required)
│   ├── extensions.py      ← Initiering av db, mail, login, csrf
│   └── __init__.py        ← Appfabrik och blueprint-registrering
├── migrations/            ← Databasens migreringsmappar
├── static/                ← CSS, JS, bilder
├── templates/             ← Jinja2-mallar
├── tools/                 ← Utvecklingsskript
├── config.py              ← Appkonfiguration
├── main.py                ← Startfil för appen / CLI
├── requirements.txt       ← Beroenden
└── README.md              ← Denna fil
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

### 🔐 Konfigurera miljövariabler

Skapa en `.env`-fil i projektets rot:

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

### 🧱 Initiera databasen

```bash
flask db init
flask db migrate -m "Första migreringen"
flask db upgrade
```

### ▶️ Starta appen

```bash
flask run
```

Besök [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🧪 Användningsöversikt

| Route             | Beskrivning                      |
| ----------------- | -------------------------------- |
| `/blog/`          | Visa blogginlägg                 |
| `/blog/new_post`  | Skapa nytt inlägg (endast admin) |
| `/blog/post/<id>` | Visa specifikt inlägg            |
| `/cv`             | CV-sektion                       |
| `/portfolio`      | Portfolio-sektion                |
| `/admin/`         | Adminpanel                       |

---

## 🔧 Teknik

- **Besöksräknare:**

  - Blogg- och portfolioposter spårar unika visningar per session (via cookies/sessions).
  - Inkluderar totalräknare för statiska sidor som `om`, `cv` m.fl.
  - Sidor som `/portfolio/<id>` och `/blog/post/<id>` uppdaterar databasen när de besöks – men endast en gång per session.

- **Förbättrad användarhantering:**

  - Token-baserad användarskapande (t.ex. via `create_user_token(email)`).
  - Automatisk lösenordssättning via e-postlänk.
  - Stöd för roller (admin, användare, prenumerant).
  - Tidsbegränsade tokens (via `itsdangerous`) med säkert salt.

- **Python 3.11+**

- **Flask** med:

  - Flask-WTF
  - Flask-Login
  - Flask-Migrate
  - Flask-Mail
  - Flask-Bootstrap
  - Flask-CaptchaFox
  - Flask-Babel

- **SQLAlchemy** + MySQL (PyMySQL)

- **Pillow** för bildhantering

- **itsdangerous** för säkra tokenflöden

- **GitHub Pages–kompatibel** layout

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

## 🚜 Kommandon via terminalen (CLI)

### ✉️ `send-blog-mails`

Skickar e-postnotiser till prenumeranter när ett blogginläggs `created_at`-tidpunkt har passerat och inlägget ännu inte har mejlats ut.

#### ✅ Användning:

```bash
flask send-blog-mails
```

> Varje inlägg markeras som skickat genom att sätta `email_sent = True`.

---

## 📆 Schemaläggning (Cron Jobs)

Vill du skicka blogginlägg automatiskt varje dag? Lägg till följande rad i din crontab för att köra kommandot kl. 21:00 varje dag:

```cron
0 21 * * * cd /home/din/sökväg/till/root-mapp && FLASK_APP=main.py FLASK_CLI=true flask send-blog-mails >> logs/send_blog_mails.log 2>&1
```

📌 **Förutsättningar:**

- Flask CLI måste fungera i din miljö.
- En `logs/`-mapp måste finnas i projektets rot.
- Miljövariabler måste vara tillgängliga via `.env` eller systeminställningar.

> Redigera din crontab med `crontab -e`.  
> I `vim`, tryck `Esc`, skriv `:wq`, och tryck Enter för att spara och avsluta.

---

## 🛠️ Utvecklingsverktyg

### 🧹 Rensa projektet (endast Windows)

Scriptet `tools/clean-project.ps1` tar bort tillfälliga filer, såsom:

- Python-cachefiler (`*.pyc`, `__pycache__`)
- Swap-/backupfiler (`*.bak`, `*~`, etc.)
- Oanvända `migrations/`-mappar (utan `versions/`)
- Test- eller tillfälliga bilder (`test`, `temp`, `debug` i `static/`)

Skapar en loggfil med tidsstämpel, t.ex. `tools/clean_log_2025-07-07_1340.txt`

```powershell
./tools/clean-project.ps1
```

### 📄 `tools/generate_docs.py`

Genererar dokumentation och snabbguider för vanliga Flask-uppgifter. Skapar `.txt` och `.md`-filer i `docs/`-mappen.

```bash
python tools/generate_docs.py
```

### 🤩 `tools/inspect_models.py`

Skriver ut alla databasens tabeller och deras kolumner. Användbart för att kontrollera databasstruktur och felsökning.

```bash
python tools/inspect_models.py
```

---

## 🤝 Bidra till projektet

1. Forka detta repo  
2. Skapa en ny feature-branch: `git checkout -b feature/din-funktion`  
3. Lägg till dina ändringar: `git commit -m 'Lagt till ny funktion'`  
4. Skicka till ditt repo: `git push origin feature/din-funktion`  
5. Skapa en Pull Request

---

## 🗒️ Att göra

1. Avregistrera sig som användare/prenumerant – Klart  
2. Förbättrad hantering av datum/tid för `posted_at` och `updated_at` – Klart  
3. Stöd för lokaliserad översättning (i18n)

---

## 📄 Licens

Detta projekt är licensierat under MIT-licensen. Se [LICENSE](LICENSE) för mer information.

---

Hör gärna av dig om du har frågor eller förslag!

