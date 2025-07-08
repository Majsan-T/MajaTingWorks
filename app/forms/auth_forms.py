# app/forms/auth_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, InputRequired, Email, Length, EqualTo, ValidationError
import re

def strong_password(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError("Lösenordet måste vara minst 8 tecken långt.")
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Lösenordet måste innehålla minst en versal.")
    if not re.search(r'[a-z]', password):
        raise ValidationError("Lösenordet måste innehålla minst en gemen.")
    if not re.search(r'\d', password):
        raise ValidationError("Lösenordet måste innehålla minst en siffra.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError("Lösenordet måste innehålla minst ett specialtecken.")

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Lösenord", validators=[DataRequired()])
    name = StringField("Namn", validators=[DataRequired()])
    role = SelectField(
        "Roll",
        choices=[("user", "Kommentera"), ("subscriber", "Prenumerera")],
        default="user",
        validators=[DataRequired()]
    )
    submit = SubmitField("Gå med")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Lösenord", validators=[DataRequired()])
    submit = SubmitField("Logga in")

class AdminCreateUserForm(FlaskForm):
    name = StringField("Namn", validators=[InputRequired()])
    email = StringField("E-post", validators=[InputRequired(), Email()])
    password = PasswordField("Lösenord", validators=[InputRequired(), Length(min=6)])
    role = SelectField("Roll", choices=[("user", "Kommentera"), ("subscriber", "Prenumerant")])
    submit = SubmitField("Skapa användare")

class SetPasswordForm(FlaskForm):
    password = PasswordField("Nytt lösenord", validators=[DataRequired(), strong_password, Length(min=12)])
    confirm_password = PasswordField("Bekräfta lösenord", validators=[
        DataRequired(), EqualTo("password", message="Lösenorden matchar inte")
    ])
    confirm = PasswordField("Bekräfta lösenord")
    submit = SubmitField("Spara lösenord")

class RequestResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Skicka återställningslänk")

class ResetPasswordForm(FlaskForm):
    password = PasswordField("Nytt lösenord", validators=[DataRequired()])
    confirm  = PasswordField(
        "Bekräfta lösenord",
        validators=[DataRequired(), EqualTo("password", message="Lösenorden måste matcha.")]
    )
    submit   = SubmitField("Återställ lösenord")