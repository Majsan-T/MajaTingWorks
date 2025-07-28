# app/forms/auth_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import Role
import re

# ======================
# ✅ LÖSENORDSVALIDERING
# ======================

def strong_password(form, field):
    """
    Validera att lösenordet är starkt:
    - Minst 8 tecken
    - Minst 1 versal, 1 gemen, 1 siffra och 1 specialtecken
    """
    password = field.data
    if len(password) < 8:
        raise ValidationError("Lösenordet måste vara minst 8 tecken långt.")
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Lösenordet måste innehålla minst en versal.")
    if not re.search(r'[a-z]', password):
        raise ValidationError("Lösenordet måste innehålla minst en gemen.")
    if not re.search(r'\d', password):
        raise ValidationError("Lösenordet måste innehålla minst en siffra.")
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        raise ValidationError("Lösenordet måste innehålla minst ett specialtecken.")


# ======================
# ✅ REGISTRERING
# ======================

class RegisterForm(FlaskForm):
    """Formulär för att skapa nytt konto (roller utan admin)."""
    name = StringField("Namn", validators=[DataRequired()])
    email = StringField("E-post", validators=[DataRequired(), Email()])
    password = PasswordField("Lösenord", validators=[DataRequired()])
    roles = SelectMultipleField(
        "Roller",
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False)
    )
    submit = SubmitField("Registrera")

    def set_role_choices(self):
        """Visa endast roller som är tillåtna vid registrering (ej admin)."""
        allowed_roles = Role.query.filter(Role.name != "admin").all()
        label_map = {
            "user": "Kommentera blogginlägg",
            "subscriber": "Prenumerera på blogginlägg"
        }
        # ✅ Använd beskrivande etiketter
        self.roles.choices = [(r.name, label_map.get(r.name, r.name.capitalize())) for r in allowed_roles]
        if self.roles.data is None:
            self.roles.data = []


# ======================
# ✅ LOGIN
# ======================

class LoginForm(FlaskForm):
    """Formulär för att logga in."""
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Lösenord", validators=[DataRequired()])
    submit = SubmitField("Logga in")


# ======================
# ✅ ADMIN – SKAPA ANVÄNDARE
# ======================

class AdminCreateUserForm(FlaskForm):
    """Formulär för admin att skapa nya användare (inkl. admin)."""
    name = StringField("Namn", validators=[DataRequired()])
    email = StringField("E-post", validators=[DataRequired(), Email()])
    roles = SelectMultipleField(
        "Roller",
        choices=[
            ("admin", "Admin"),
            ("subscriber", "Prenumerant"),
            ("user", "Användare")
        ],
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False)
    )
    submit = SubmitField("Skapa användare")

    def set_role_choices(self):
        """Hämta alla roller dynamiskt (inkl. admin)."""
        self.roles.choices = [(r.name, r.name.capitalize()) for r in Role.query.all()]


# ======================
# ✅ SÄTT NYTT LÖSENORD
# ======================

class SetPasswordForm(FlaskForm):
    """Sätt nytt lösenord (via återställningslänk eller admininbjudan)."""
    password = PasswordField("Nytt lösenord", validators=[DataRequired(), strong_password, Length(min=12)])
    confirm_password = PasswordField("Bekräfta lösenord", validators=[
        DataRequired(), EqualTo("password", message="Lösenorden matchar inte")
    ])
    confirm = PasswordField("Bekräfta lösenord")
    submit = SubmitField("Spara lösenord")


# ======================
# ✅ LÖSENORDSÅTERSTÄLLNING
# ======================

class RequestResetForm(FlaskForm):
    """Formulär för att begära återställningslänk via e-post."""
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Skicka återställningslänk")


class ResetPasswordForm(FlaskForm):
    """Återställ lösenord efter återställningslänk."""
    password = PasswordField("Nytt lösenord", validators=[DataRequired()])
    confirm = PasswordField(
        "Bekräfta lösenord",
        validators=[DataRequired(), EqualTo("password", message="Lösenorden måste matcha.")]
    )
    submit = SubmitField("Återställ lösenord")


# ======================
# ✅ GENERELLT RADERINGSFORMULÄR
# ======================

class DeleteForm(FlaskForm):
    """Enkelt formulär för att radera resurser (t.ex. användare, kommentarer)."""
    submit = SubmitField("Ta bort")
