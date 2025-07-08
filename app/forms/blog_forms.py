# app/forms/blog_forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, BooleanField, SubmitField, TextAreaField, DateField
from wtforms.validators import DataRequired, Optional, Length, ValidationError
from wtforms.fields.simple import HiddenField
from app.utils.helpers import get_local_now
from datetime import datetime
from bs4 import BeautifulSoup

# Anpassad validator för Quill
def QuillContentRequired(form, field):
    if not field.data:
        raise ValidationError('Inlägget kan inte vara tomt.')
    soup = BeautifulSoup(field.data, 'html.parser')
    if not soup.get_text(strip=True):
        raise ValidationError('Inlägget kan inte vara tomt.')


class BlogPostForm(FlaskForm):
    title = StringField("Titel", validators=[DataRequired(), Length(max=100)])
    subtitle = StringField("Underrubrik", validators=[DataRequired(), Length(max=200)])
    body = TextAreaField("Inlägg", validators=[QuillContentRequired])

    img_file = FileField("Bild (Valfritt)", validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], "Endast bildfiler är tillåtna.")
    ])
    delete_image = BooleanField("Ta bort rubrikbild (ersätts med defaultbild)")

    date = DateField("Datum", format='%Y-%m-%d', validators=[DataRequired()])
    time = StringField("Klockslag (HH:MM)", validators=[DataRequired()])

    category = SelectField("Kategori", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Skicka")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_submitted() and not self.date.data:
            self.date.data = get_local_now().date()

class BlogCategoryForm(FlaskForm):
    name = StringField("Intern namn (URL-vänligt)", validators=[DataRequired()])
    title = StringField("Visningsnamn", validators=[DataRequired()])
    description = TextAreaField("Beskrivning", validators=[Optional()])
    image = FileField("Kategori-bild", validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], "Endast bildfiler är tillåtna.")
    ])
    delete_image = BooleanField("Ta bort bild")
    replace_image = BooleanField("Ersätt bild")
    submit = SubmitField("Spara")

class CategoryFilterForm(FlaskForm):
    category = SelectField(
        "Kategori",
        choices=[],    # här sätter vi .choices i vyn
        coerce=int,    # ser till att value kommer som int
        validators=[Optional()]
    )
