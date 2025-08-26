from flask import Flask, render_template, redirect, url_for, request, flash, session
import datetime as dt
import calendar 
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey, Date
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

# now = dt.datetime.now()
# year = now.year
# days_in_year = 366 if calendar.isleap(year) else 365


def get_days_by_month(year):
    days_by_month = {}
    for month in range(1, 13):
        #print(f"Processing year: {year}, month: {month}")  # Debug output
        num_days = calendar.monthrange(year, month)[1]
        days_by_month[calendar.month_name[month]] = list(range(1, num_days + 1))
    return days_by_month

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


#Create activity log data model 

class ActivityLog(db.Model):
    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey('activity.id'), nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)

    # Relationship to link back to the activity
    activity: Mapped[Activity] = relationship("Activity", backref="logs", lazy=True)


# create a user loader callback 
@login_manager.user_loader
def load_user(id):
    with db.session() as session:
     return session.get(User, int(id))

def admin_only(f):
    @wraps(f)  
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            abort(403)  
        return f(*args, **kwargs)  
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
            return redirect(url_for('register'))  
        
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

        session['name'] = name  
        return redirect(url_for("home", name=name)) 

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
@login_required
def update_activity_color(activity_id):
    new_color = request.form.get('activity_color')
    activity = Activity.query.get(activity_id)

    if not activity:
        return "Activity not found", 404

    if activity.user_id != current_user.id:
        return "Forbidden", 403

    activity.color = new_color
    db.session.commit()
    return "Color updated", 200  # ✅ plain response for JS, no redirect


@app.route("/log_activity_day", methods=["POST"])
@login_required
def log_activity_day():
    activity_id = request.form.get("activity_id")
    date_str = request.form.get("date")
    date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()

    existing_log = ActivityLog.query.filter_by(
        activity_id=activity_id,
        date=date,
        user_id=current_user.id
    ).first()

    if existing_log:
        print("Already logged")
    else:
        new_log = ActivityLog(
            activity_id=activity_id,
            date=date,
            user_id=current_user.id
        )
        db.session.add(new_log)
        db.session.commit()
        print("Activity logged")

    return "Logged", 200  




@app.route('/track')
def track():
    activities = Activity.query.filter_by(user_id=current_user.id).all()
    logs = ActivityLog.query.filter_by(user_id=current_user.id).all()

    today = dt.date.today()
    year = request.args.get("year", type=int, default=today.year)
    month_num = request.args.get("month", type=int, default=today.month)

    # weekday of 1st day (Mon=0..Sun=6) and number of days in month
    first_weekday, num_days = calendar.monthrange(year, month_num)

    # 6 full rows -> 42 cells
    TOTAL = 42
    leading_blanks = first_weekday                     # blanks before day 1
    trailing_blanks = TOTAL - leading_blanks - num_days  # blanks after last day

    # Maps
    month_numbers = {name: i for i, name in enumerate(calendar.month_name) if name}
    month_names = {i: name for name, i in month_numbers.items()}
    month_name = month_names[month_num]

    # Prev/Next
    prev_month = 12 if month_num == 1 else month_num - 1
    prev_year  = year - 1 if month_num == 1 else year
    next_month = 1 if month_num == 12 else month_num + 1
    next_year  = year + 1 if month_num == 12 else year

    log_data = [{
        "activity_id": log.activity_id,
        "date": log.date.isoformat(),
        "activity": {"color": log.activity.color}
    } for log in logs]

    return render_template(
        "tracking.html",
        year=year,
        month=month_name,
        month_num=month_num,
        num_days=num_days,
        first_weekday=first_weekday,
        leading_blanks=leading_blanks,
        trailing_blanks=trailing_blanks,
        month_numbers=month_numbers,
        activities=activities,
        logs=log_data,
        prev_month=prev_month, prev_year=prev_year,
        next_month=next_month, next_year=next_year
    )






if (__name__) == "__main__":
    app.run(debug=True)