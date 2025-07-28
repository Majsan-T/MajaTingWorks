# app/forms/shared_forms.py
from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional

# ===================================================
# ✅ ADMIN – SKAPA ANVÄNDARE
# ===================================================
class AdminUserForm(FlaskForm):
    """Formulär för att skapa en ny admin-användare."""
    email = StringField("E-post", validators=[DataRequired(), Email()])
    name = StringField("Namn", validators=[DataRequired()])
    password = PasswordField("Lösenord", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Skapa admin")

# ===================================================
# ✅ KOMMENTARER – SKAPA ELLER REDIGERA
# ===================================================
class CommentForm(FlaskForm):
    """Formulär för att skapa eller redigera en kommentar."""
    comment_text = TextAreaField("Kommentar", validators=[DataRequired()])
    submit = SubmitField("Skicka kommentar")

# ===================================================
# ✅ GEMENSAMT FORMULÄR FÖR RADERING
# ===================================================
class DeleteForm(FlaskForm):
    """Standardformulär för att bekräfta radering av en post."""
    submit = SubmitField("Ja, ta bort")

# ===================================================
# ✅ GODKÄNN KOMMENTARER (ANVÄNDS I ADMIN)
# ===================================================
class ApproveForm(FlaskForm):
    """Formulär för att godkänna en flaggad kommentar."""
    submit = SubmitField("Godkänn")

# ===================================================
# ✅ UPPDATERA ANVÄNDARE (FYLLS DYNAMISKT I ADMIN)
# ===================================================
class UserUpdateForm(FlaskForm):
    """Tomt formulär – fälten hanteras dynamiskt i adminpanelen."""
    pass

# ===================================================
# ✅ TOMT FORMULÄR (ANVÄNDS FÖR ENKLA POST-REQUESTS)
# ===================================================
class EmptyForm(FlaskForm):
    """Används för enkla POST-anrop där inga fält behövs (t.ex. aktivera/inaktivera)."""
    pass

# ===================================================
# ✅ CV – REDIGERING AV INNEHÅLL
# ===================================================
class CvEditForm(FlaskForm):
    """Formulär för att redigera CV-innehåll i adminpanelen."""
    class Meta:
        csrf = True
        csrf_time_limit = None    # Inaktiverar CSRF-timeout tillfälligt (för långa sessioner)
    about = TextAreaField("Om mig")
    experience = TextAreaField("Erfarenhet")
    education = TextAreaField("Utbildning")
    awards = TextAreaField("Certifieringar")
    skills = TextAreaField("Kunskaper")
    interests = TextAreaField("Intressen")
    submit = SubmitField("Spara")

# ===================================================
# ✅ BILDER – RADERA EN UPPLADDAD FIL
# ===================================================
class ImageDeleteForm(FlaskForm):
    """Formulär för att ta bort en uppladdad bild (t.ex. i adminpanelen)."""
    folder = HiddenField(validators=[DataRequired()])
    filename = HiddenField(validators=[DataRequired()])
    submit = SubmitField("Ta bort")