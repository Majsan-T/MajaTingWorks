# app/forms/blog_forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, BooleanField, SubmitField, TextAreaField, DateField
from wtforms.validators import DataRequired, Optional, Length, ValidationError
from app.utils.helpers import get_local_now
from datetime import datetime
from bs4 import BeautifulSoup

# ===================================================
# ✅ ANPASSAD VALIDATOR FÖR QUILL (Tomma <p> tillåts ej)
# ===================================================
def QuillContentRequired(form, field):
    """Validera att Quill-innehållet inte bara är tomma taggar."""
    if not field.data:
        raise ValidationError('Inlägget kan inte vara tomt.')
    soup = BeautifulSoup(field.data, 'html.parser')
    if not soup.get_text(strip=True):
        raise ValidationError('Inlägget kan inte vara tomt.')

# ===================================================
# ✅ FORMULÄR FÖR BLOGGINLÄGG
# ===================================================
class BlogPostForm(FlaskForm):
    """Formulär för att skapa eller redigera blogginlägg."""
    title = StringField("Titel", validators=[DataRequired(), Length(max=100)])
    subtitle = StringField("Underrubrik", validators=[DataRequired(), Length(max=200)])
    body = TextAreaField("Inlägg", validators=[QuillContentRequired])

    # === Bildhantering ===
    img_file = FileField("Bild (Valfritt)", validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], "Endast bildfiler är tillåtna.")
    ])
    delete_image = BooleanField("Ta bort rubrikbild (ersätts med defaultbild)")

    # === Datum & tid (styr schemaläggning) ===
    date = DateField("Datum", format='%Y-%m-%d', validators=[DataRequired()])
    time = StringField("Klockslag (HH:MM)", validators=[DataRequired()])

    # === Kategori (hämtas dynamiskt i vyn) ===
    category = SelectField("Kategori", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Skicka")

    def __init__(self, *args, **kwargs):
        """Sätt dagens datum som standard när formuläret laddas."""
        super().__init__(*args, **kwargs)
        if not self.is_submitted() and not self.date.data:
            self.date.data = get_local_now().date()

# ===================================================
# ✅ FORMULÄR FÖR BLOGGKATEGORIER
# ===================================================
class BlogCategoryForm(FlaskForm):
    """Formulär för att skapa eller redigera bloggens kategorier."""
    name = StringField("Intern namn (URL-vänligt)", validators=[DataRequired()])
    title = StringField("Visningsnamn", validators=[DataRequired()])
    description = TextAreaField("Beskrivning", validators=[Optional()])

    # === Bild för kategorin ===
    image = FileField("Kategori-bild", validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], "Endast bildfiler är tillåtna.")
    ])
    delete_image = BooleanField("Ta bort bild")
    replace_image = BooleanField("Ersätt bild")
    submit = SubmitField("Spara")

# ===================================================
# ✅ FILTERFORMULÄR FÖR LISTNING AV INLÄGG
# ===================================================
class CategoryFilterForm(FlaskForm):
    """Formulär för att filtrera blogginlägg per kategori."""
    category = SelectField(
        "Kategori",
        choices=[],    # här sätter vi .choices i vyn
        coerce=int,    # ser till att value kommer som int
        validators=[Optional()]
    )
