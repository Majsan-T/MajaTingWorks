# app/forms/contact_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField, TextAreaField
from wtforms.validators import DataRequired, Email

# ===================================================
# ✅ KONTAKTFORMULÄR – FÖR KONTAKTSIDAN
# ===================================================
class ContactForm(FlaskForm):
    """Formulär för att skicka meddelande via kontaktsidan."""
    name = StringField(
        "Namn",
        validators=[DataRequired()]  # Namn måste anges
    )
    email = StringField(
        "E-postadress",
        validators=[DataRequired(), Email()]  # Måste vara giltig e-post
    )
    subject = StringField(
        "Ämne",
        validators=[DataRequired()]  # Ämnesrad är obligatorisk
    )
    message = TextAreaField(
        "Meddelande",
        validators=[DataRequired()]  # Själva meddelandet får inte vara tomt
    )
    captcha_token = HiddenField()
    # 👆 Token används av CaptchaFox (eller annan captcha) för att förhindra spam

    submit = SubmitField("Skicka Meddelande")  # Skickar formuläret
