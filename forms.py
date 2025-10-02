from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, RadioField, ValidationError
from wtforms.validators import DataRequired, URL, Length, Optional
from flask_ckeditor import CKEditorField



class ActivityForm(FlaskForm):
    name = StringField("Activity", validators=[DataRequired()], render_kw={"placeholder": "Activity Name"})
    icon_ref = StringField(validators=[Optional()])    
    submit = SubmitField("Do It!")

class RegisterForm(FlaskForm):

    name= StringField('Name', validators=[DataRequired()],render_kw={"placeholder": "Name"})
    email =  StringField('Email', validators=[DataRequired()], render_kw={"placeholder": "Email"})
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters long.")],render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email =  StringField('Email', validators=[DataRequired()], render_kw={"placeholder": "Email"} )
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters long.")],render_kw={"placeholder": "Password"})
    submit = SubmitField('Log in')


