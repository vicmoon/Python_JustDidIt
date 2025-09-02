from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, RadioField
from wtforms.validators import DataRequired, URL, Length
from flask_ckeditor import CKEditorField

ICON_CHOICES = [
    ("balloon.png", "🎈 Balloon"),
    ("bike.png", "🚲 Bike"),
    ("book.png", "📖 Book"),
    ("briefcase.png", "💼 Briefcase"),
    ("calculator.png", "🧮 Calculator"),
    ("camera.png", "📷 Camera"),
    ("cassette.png", "📼 Cassette"),
    ("food.png", "🍽️ Food"),
    ("globe.png", "🌍 Globe"),
    ("lifestyle.png", "✨ Lifestyle"),
    ("magazine.png", "📰 Magazine"),
    ("medical.png", "⚕️ Medical"),
    ("microfon.png", "🎤 Microphone"),   
    ("music.png", "🎵 Music"),
    ("navigation.png", "🧭 Navigation"),
    ("networking.png", "🌐 Networking"),
    ("news.png", "🗞️ News"),
    ("photo.png", "📸 Photo"),
    ("pig.png", "🐷 Pig"),
    ("popcorn.png", "🍿 Popcorn"),
    ("productivity.png", "📊 Productivity"),
    ("research.png", "🔬 Research"),
    ("shopping.png", "🛍️ Shopping"),
    ("sports.png", "🏀 Sports"),
    ("travel.png", "✈️ Travel"),
    ("weather.png", "☀️ Weather"),
]


class ActivityForm(FlaskForm):
    name = StringField("Activity", validators=[DataRequired()], render_kw={"placeholder": "Activity Name"})
    icon = RadioField("Icon", choices=ICON_CHOICES, validators=[DataRequired()])
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


