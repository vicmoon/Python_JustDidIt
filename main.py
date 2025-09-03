from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
import datetime as dt
import calendar
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, Date, text
from forms import ActivityForm, LoginForm, RegisterForm
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import my_creds
import json
from collections import defaultdict


# ---------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = my_creds.SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///activities.db"

db = SQLAlchemy(app)
Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Make current year available in all templates
app.jinja_env.globals['current_year'] = dt.datetime.utcnow().year


# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------
class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False, unique=True)
    icon = db.Column(db.String(120), nullable=False)
    # NEW: Iconify identifier like "mdi:run" or "tabler:book"

    icon_ref = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))

    activities: Mapped[list[Activity]] = relationship("Activity", backref="user", lazy=True)


class ActivityLog(db.Model):
    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey('activity.id'), nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)

    activity: Mapped[Activity] = relationship("Activity", backref="logs", lazy=True)


# ---------------------------------------------------------------------
# User loader
# ---------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------------------------------------------------------------
# DB init
# ---------------------------------------------------------------------
with app.app_context():
    db.create_all()


# ---------------------------------------------------------------------
# Auth guard: require login except for public endpoints
# ---------------------------------------------------------------------
@app.before_request
def require_login():
    public = {'home', 'login', 'register', 'logout', 'static'}
    if request.endpoint in public or request.endpoint is None:
        return
    if not current_user.is_authenticated:
        next_url = request.full_path if request.query_string else request.path
        return redirect(url_for('login', next=next_url))


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not name or not email or not password:
            flash("All fields are required", "danger")
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("User already exists. Please log in.", "warning")
            return redirect(url_for('login'))

        hashed_pass = generate_password_hash(password, method='scrypt', salt_length=8)
        new_user = User(name=name, email=email, password=hashed_pass)

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)

        session['name'] = name
        return redirect(url_for("home"))

    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = request.form.get('email')
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("That email does not exist, please try again.", "danger")
            return redirect(url_for('login'))

        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.', "danger")
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for("track"))

    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/add-activity", methods=["GET", "POST"])
@login_required
def add_activity():
    form = ActivityForm()
    icon_file = form.icon.data or None
    icon_ref  = form.icon_ref.data or None


    if form.validate_on_submit():
        new_activity = Activity(
            name=form.name.data.strip(),
            icon=icon_file if not icon_ref else None,
            icon_ref=icon_ref,
            user_id=current_user.id
        )
        db.session.add(new_activity)
        db.session.commit()
        flash('Activity added!', "success")
        return redirect(url_for('track'))

    return render_template("add_activity.html", form=form)


@app.route("/log_activity_day", methods=["POST"])
@login_required
def log_activity_day():
    data = request.get_json()
    try:
        activity_id = int(data.get('activity_id'))
        date_str = dt.date.fromisoformat(data.get('date'))
    except Exception as e:
        return jsonify(ok=False, error="Bad payload"), 400
    

    #check that the user owns the activity 

    activity = Activity.query.filter_by(id=activity_id, user_id=current_user.id).first()
    if not activity:
        return jsonify(ok=False, error="Not your activity"), 403
    

    existing = ActivityLog.query.filter_by(activity_id=activity_id, date=date_str, user_id=current_user.id).first()
    
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify(ok=True, state="removed", activity_id=activity_id)
  
    else:
        new_log = ActivityLog(activity_id=activity_id, date=date_str, user_id=current_user.id)
        db.session.add(new_log)
        db.session.commit()
        return jsonify(ok=True, state="added", activity_id=activity_id, icon=activity.icon)

    

@app.route('/track')
@login_required
def track():

    today = dt.date.today()
    year = request.args.get("year", type=int, default=today.year)
    month_num = request.args.get("month", type=int, default=today.month)

    first_weekday, num_days = calendar.monthrange(year, month_num)
    start = dt.date(year, month_num, 1)
    end = dt.date(year + (month_num == 12), (month_num % 12) + 1, 1)  # first day next month

    
    activities = Activity.query.filter_by(user_id=current_user.id).all()
    logs = (
        ActivityLog.query
        .filter(
            ActivityLog.user_id == current_user.id,
            ActivityLog.date >= start,
            ActivityLog.date < end
        ).all()
    )

    # for server-side icons
    icons_by_date = {}
    for log in logs:
        icons_by_date.setdefault(log.date.isoformat(), []).append({
            "activity_id": log.activity_id,
            "icon": log.activity.icon,
})

    # for client-side JS
    logs_json = [
        {
            "date": log.date.isoformat(),
            "activity_id": log.activity_id,
            "icon": log.activity.icon
        }
        for log in logs
    ]



    TOTAL = 42
    leading_blanks = first_weekday
    trailing_blanks = TOTAL - leading_blanks - num_days

    month_numbers = {name: i for i, name in enumerate(calendar.month_name) if name}
    month_names = {i: name for name, i in month_numbers.items()}
    month_name = month_names[month_num]

    prev_month = 12 if month_num == 1 else month_num - 1
    prev_year = year - 1 if month_num == 1 else year
    next_month = 1 if month_num == 12 else month_num + 1
    next_year = year + 1 if month_num == 12 else year


    return render_template(
        "track.html",
        year=year,
        month=month_name,
        month_num=month_num,
        num_days=num_days,
        first_weekday=first_weekday,
        leading_blanks=leading_blanks,
        trailing_blanks=trailing_blanks,
        month_numbers=month_numbers,
        activities=activities,
        icons_by_date=icons_by_date,
        logs=logs_json,
        prev_month=prev_month, prev_year=prev_year,
        next_month=next_month, next_year=next_year
    )


# ---------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
