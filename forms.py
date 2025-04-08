from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp

# password strength regex
PASSWORD_REGEX = r"^(?=.*[A-Z])(?=.*\d).{8,}$"

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters"),
            Regexp(PASSWORD_REGEX, message="Password must include an uppercase letter and a number."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class ResetRequestForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")

class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8),
            Regexp(PASSWORD_REGEX, message="Password must include an uppercase letter and a number."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm New Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Reset Password")
