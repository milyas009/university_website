from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from application.models import User

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[
        DataRequired(),
        Email(message="Please enter a valid email address")
    ])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[
        DataRequired(),
        Email(message="Please enter a valid email address")
    ])
    password = PasswordField("Password", validators=[
        DataRequired(),
        Length(min=6, message="Password must be at least 6 characters long")
    ])
    password_confirm = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    first_name = StringField("First Name", validators=[
        DataRequired(),
        Length(min=2, max=55, message="Name must be between 2 and 55 characters")
    ])
    last_name = StringField("Last Name", validators=[
        DataRequired(),
        Length(min=2, max=55, message="Name must be between 2 and 55 characters")
    ])
    submit = SubmitField("Register")

    def validate_email(self, email):
        user = User.objects(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')