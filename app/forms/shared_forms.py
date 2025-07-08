# app/forms/shared_forms.py
from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional

class AdminUserForm(FlaskForm):
    email = StringField("E-post", validators=[DataRequired(), Email()])
    name = StringField("Namn", validators=[DataRequired()])
    password = PasswordField("Lösenord", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Skapa admin")

class CommentForm(FlaskForm):
    comment_text = TextAreaField("Kommentar", validators=[DataRequired()])
    submit = SubmitField("Skicka kommentar")

class DeleteForm(FlaskForm):
    submit = SubmitField("Ja, ta bort")

class ApproveForm(FlaskForm):
    submit = SubmitField("Godkänn")

class UserUpdateForm(FlaskForm):
    pass

class CvEditForm(FlaskForm):
    class Meta:
        csrf = True
        csrf_time_limit = None  # <i class="bi bi-arrow-left"></i> inaktiverar CSRF-timeout tillfälligt
    about = TextAreaField("Om mig")
    experience = TextAreaField("Erfarenhet")
    education = TextAreaField("Utbildning")
    awards = TextAreaField("Certifieringar")
    skills = TextAreaField("Kunskaper")
    interests = TextAreaField("Intressen")
    submit = SubmitField("Spara")

class ImageDeleteForm(FlaskForm):
    folder = HiddenField(validators=[DataRequired()])
    filename = HiddenField(validators=[DataRequired()])
    submit = SubmitField("Ta bort")