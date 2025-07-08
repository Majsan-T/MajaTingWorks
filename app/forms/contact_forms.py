# app/forms/contact_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField, TextAreaField
from wtforms.validators import DataRequired, Email

class ContactForm(FlaskForm):
    name = StringField("Namn", validators=[DataRequired()])
    email = StringField("E-postadress", validators=[DataRequired(), Email()])
    subject = StringField("Ämne", validators=[DataRequired()])
    message = TextAreaField("Meddelande", validators=[DataRequired()])
    captcha_token = HiddenField()  # 👈 captchafox token
    submit = SubmitField("Skicka Meddelande")