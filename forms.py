from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, URL, Length
from flask_ckeditor import CKEditorField

class ActivityForm(FlaskForm):
    name = StringField("Activity", validators=[DataRequired()])
    color = StringField("Color", validators=[DataRequired()])
    
    progress_choices = [("new", "New"), ("in_progress", "In Progress"), ("completed", "Completed")]
    progress = SelectField("Progress", choices=progress_choices, validators=[DataRequired()])
    
    submit = SubmitField("Do It!")

class RegisterForm(FlaskForm):

    name= StringField('Name', validators=[DataRequired()])
    email =  StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters long.")])
    submit = SubmitField('Register')



class LoginForm(FlaskForm):
    email =  StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters long.")])
    submit = SubmitField('Log in')


