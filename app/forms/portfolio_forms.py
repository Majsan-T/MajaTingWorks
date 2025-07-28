from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, BooleanField, SubmitField, TextAreaField, HiddenField, RadioField
from wtforms.validators import DataRequired, Optional
from app.models import Category

# ===================================================
# ✅ FORMULÄR FÖR PORTFOLIO-INLÄGG
# ===================================================
class PortfolioForm(FlaskForm):
    """Formulär för att skapa eller redigera ett portfolio-inlägg."""
    title = StringField("Titel", validators=[DataRequired()])
    category = SelectField("Kategori", coerce=int, validators=[DataRequired()])
    description = HiddenField("Beskrivning", validators=[DataRequired()])  # Quill- eller rich-text hanteras som hidden

    # === Bildhantering (huvudbild & kategoribild) ===
    image = FileField("Ladda upp ny bild", validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], "Endast bildfiler tillåtna.")])
    category_image = FileField("Kategori‐bild", validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], "Endast bildfiler tillåtna.")])
    replace_image = BooleanField("Ersätt bild")
    delete_image = BooleanField("Ta bort rubrikbild (ersätts med defaultbild för kategorin)")

    # === Välj hur bilden ska hanteras ===
    image_action = RadioField("Bildhantering", choices=[
        ("keep", "Behåll nuvarande bild"),
        ("replace", "Ersätt med ny bild"),
        ("delete", "Ta bort bild utan att ersätta")
    ], default="keep")
    submit = SubmitField("Spara")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category.choices = [(cat.id, cat.title) for cat in Category.query.order_by(Category.title).all()]

# ===================================================
# ✅ FORMULÄR FÖR PORTFOLIO-KATEGORIER
# ===================================================
class CategoryForm(FlaskForm):
    """Formulär för att skapa eller redigera en portfolio-kategori."""
    name = StringField("Intern namn (URL-vänligt)", validators=[DataRequired()])
    title = StringField("Visningsnamn", validators=[DataRequired()])
    description = TextAreaField("Beskrivning", validators=[Optional()])

    # === Genrebild för kategorin ===
    image = FileField("Genrebild", validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], "Endast bildfiler tillåtna.")])
    delete_image = BooleanField("Ta bort bild")
    replace_image = BooleanField("Ersätt bild")
    submit = SubmitField("Spara")

# ===================================================
# ✅ FILTERFORMULÄR (ANVÄNDS I ADMIN ELLER LISTNING)
# ===================================================
class CategorySelectForm(FlaskForm):
    """Formulär för att filtrera portfolio-inlägg baserat på kategori."""
    category = SelectField('Kategori', choices=[], default="", validators=[Optional()])
    submit = SubmitField("Visa Inlägg")

    def __init__(self, categories, *args, **kwargs):
        """Sätt kategorilistan vid initiering."""
        super().__init__(*args, **kwargs)
        self.category.choices = [(cat, cat) for cat in categories]

# ===================================================
# ✅ FILTERFORMULÄR (ALTERNATIV VARIANT FÖR LISTNING)
# ===================================================
class CategorySelectItem(FlaskForm):
    """Variant av filterformulär för enklare listning av portfolio-inlägg."""
    category = SelectField('Kategori', choices=[], default="", validators=[Optional()])
    submit = SubmitField("Visa")

    def __init__(self, categories, *args, **kwargs):
        """Sätt kategorilistan vid initiering."""
        super().__init__(*args, **kwargs)
        self.category.choices = [(cat, cat) for cat in categories]
