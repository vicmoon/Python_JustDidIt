from flask import Flask, render_template
import datetime as dt
import calendar
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Column, Integer, String, UniqueConstraint
from wtforms import StringField, SubmitField, SelectField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
import my_creds


app = Flask(__name__)
app.config['SECRET_KEY'] = my_creds.SECRET_KEY

now = dt.datetime.now()
year = now.year
days_in_year = 366 if calendar.isleap(year) else 365

# print(days_in_year)
def get_days():
    days = []
    for i in range(1, days_in_year + 1):
        days.append(i)
    return days

    # return [i for i in range(1, days_in_year + 1)]

#created database 

class Base(DeclarativeBase):
    pass

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///activities.db"
db = SQLAlchemy(app)

class Activity(db.Model):
    __tablename__ = "activity"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False, unique=True)
    color = db.Column(db.String(250), nullable=False)  # Store selected color as text
    progress = db.Column(db.String(250), nullable=False)  # Store selected progress as text

with app.app_context():
    db.create_all()


#create activity form 

class ActivityForm(FlaskForm):
    name = StringField("Activity", validators=[DataRequired()])
    
    color_choices = [("red", "Red"), ("blue", "Blue"), ("green", "Green"), ("yellow", "Yellow")]
    progress_choices = [("not_started", "Not Started"), ("in_progress", "In Progress"), ("completed", "Completed")]

    color = SelectField("Color", choices=color_choices, validators=[DataRequired()])
    progress = SelectField("Progress", choices=progress_choices, validators=[DataRequired()])
    
    submit = SubmitField("Start tracking")
#display the form for the user to set their activities to track 
#
        
@app.route("/")
def home():
    
    return render_template("index.html")
@app.route("/add_activity")

def add_activity():
    form = ActivityForm()
    if form.validate_on_submit():
        new_activity = Activity(
            name = form.name.data, 
            color= form.color.data, 
            progress = form.progress.data
        )

        db.session.add(new_activity)
        db.session.commit()
        print("Activity added")
        return redirect(url_for('home'))
    return render_template("add_activity.html", form=form)




@app.route('/track')
def track():
    return render_template("tracking.html", days=get_days())
if (__name__) == "__main__":
    app.run(debug=True)