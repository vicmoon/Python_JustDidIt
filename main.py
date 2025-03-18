from flask import Flask, render_template, redirect, url_for, request, flash, session
import datetime as dt
import calendar
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey
from wtforms import StringField, SubmitField, SelectField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from forms import ActivityForm, LoginForm, RegisterForm
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import my_creds


app = Flask(__name__)
app.config['SECRET_KEY'] = my_creds.SECRET_KEY
login_manager = LoginManager()

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
login_manager.init_app(app)
Bootstrap(app)

class Activity(db.Model):
    __tablename__ = "activity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False, unique=True)
    color: Mapped[str] = mapped_column(String(10), nullable=False) 
    # progress: Mapped[str] = mapped_column(String(250), nullable=False)  

    #foreign key linking the activity to the user who created it 
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))

    #relationship to access all the activities created by the user 

    activities: Mapped[list[Activity]] = relationship("Activity", backref="user", lazy=True)



# create a user loader callback 
@login_manager.user_loader
def load_user(id):
    with db.session() as session:
     return session.get(User, int(id))

def admin_only(f):
    @wraps(f)  # ✅ Preserves function metadata
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            abort(403)  # ❌ Access denied
        return f(*args, **kwargs)  # ✅ Allow access
    return decorated




with app.app_context():
    db.create_all()



# ...............................................................................

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
 
    if form.validate_on_submit():
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        print()

        if not name or not email or not password:
            flash("All fields are required", "danger")
            return redirect(url_for('register'))  # Redirect instead of returning raw text
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("User already exists. Please log in.", "warning")
            return redirect(url_for('login'))
        
        # Hash password and create new user
        hashed_pass = generate_password_hash(password, method='scrypt', salt_length=8)
        new_user = User(name=name, email=email, password=hashed_pass)
        print(f"{name}, {email}, {password}")

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)

        session['name'] = name  # Store name in session
        return redirect(url_for("home", name=name))  # redirect(url_for("home"))

    print("Something was wrong")
    return render_template("register.html", form=form)



@app.route('/login', methods=['GET','POST'])
def login():

    form = LoginForm()

    if form.validate_on_submit():
        email = request.form.get('email')
        password= request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))

        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)

            return redirect(url_for("track"))
            
        
    return render_template("login.html", form=form)



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/")
def home():  
    return render_template("index.html")


@app.route("/add-activity", methods=["GET", "POST"])
def add_activity():
    form = ActivityForm()
    if form.validate_on_submit():

        new_activity = Activity(
            name = form.name.data, 
            color= form.color.data,
            # progress = form.progress.data,
            user_id=current_user.id
        )

        db.session.add(new_activity)
        db.session.commit()
        flash('Activity added!')
        return redirect(url_for('track'))
    return render_template("add_activity.html", form=form)



@app.route('/update_activity_color/<int:activity_id>', methods=['POST'])
def update_activity_color(activity_id):
    new_color = request.form.get('activity_color')
    activity = Activity.query.get(activity_id)


    if activity.user_id != current_user.id:
        abort(403)

    if activity:
        activity.color = new_color
        db.session.commit()
        flash("Color updated successfully!", "success")
    else:
        flash("Activity not found.", "danger")
    return redirect(url_for('track'))



@app.route('/track')
def track():
    activities = Activity.query.filter_by(user_id=current_user.id).all()

    return render_template("tracking.html", days=get_days(), activities=activities)
if (__name__) == "__main__":
    app.run(debug=True)