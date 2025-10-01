from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify, current_app
import calendar
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, Date, text, event
from sqlalchemy.engine import Engine
from forms import ActivityForm, LoginForm, RegisterForm
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
# import my_creds
import json
from collections import defaultdict
import datetime as dt
from datetime import date
import sqlite3
import os
from urllib.parse import urlparse


# ---------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = my_creds.SECRET_KEY
# --- PostgreSQL on Railway, SQLite locally fallback ---
raw_db_url = os.getenv("DATABASE_URL", "sqlite:///activities.db")

# Railway sometimes provides `postgres://...` – SQLAlchemy wants `postgresql+psycopg2://...`
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif raw_db_url.startswith("postgresql://"):
    # make explicit driver for SQLAlchemy 2.x
    raw_db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = raw_db_url
# optional but recommended
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}


csrf = CSRFProtect(app)                           # enable CSRF globally

@app.context_processor
def inject_csrf_token():
    # makes csrf_token() available in ALL templates
    return dict(csrf_token=generate_csrf)

db = SQLAlchemy(app)

# --- Enable SQLite foreign keys for every new connection -------------
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Only for SQLite connections
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Make current year available in all templates
app.jinja_env.globals['current_year'] = dt.datetime.utcnow().year


# ---------------------------------------------------------------------
# --- Models ---
class Activity(db.Model):
    __tablename__ = "activity"

    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(250), nullable=False)
    icon_ref = db.Column(db.String(100), nullable=False)  # Iconify-only -> NOT NULL
    user_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='uq_activity_user_name'),
    )

    # ORM cascade; DB cascade happens via FK on ActivityLog (requires PRAGMA ON)
    logs = db.relationship(
        "ActivityLog",
        back_populates="activity",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True,
    )


class ActivityLog(db.Model):
    __tablename__ = "activity_log"

    id          = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(
        db.Integer,
        db.ForeignKey("activity.id", ondelete="CASCADE"),
        nullable=False,
    )
    date    = db.Column(db.Date, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    activity = db.relationship("Activity", back_populates="logs", lazy=True)


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))

    activities: Mapped[list[Activity]] = relationship("Activity", backref="user", lazy=True)


# ---------------------------------------------------------------------
# User loader
# ---------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------------------------------------------------------------
# DB init + verify PRAGMA
# ---------------------------------------------------------------------
with app.app_context():
    db.create_all()
    # Log PRAGMA to confirm FK enforcement is ON (should print 1)
    fk = db.session.execute(text("PRAGMA foreign_keys")).scalar()
    current_app.logger.info("SQLite PRAGMA foreign_keys=%s", fk)


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

        if not check_password_hash(user.password, password):
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
    icon_ref  = form.icon_ref.data or None

    if form.validate_on_submit():
        new_activity = Activity(
            name=form.name.data.strip(),
            icon_ref=icon_ref,
            user_id=current_user.id
        )
        db.session.add(new_activity)
        db.session.commit()
        flash('Activity added!', "success")
        return redirect(url_for('track'))

    if request.method == "POST":
        flash(f"Please fix {form.errors}", "danger")

    return render_template("add_activity.html", form=form)


@app.post("/log_activity_day")
@login_required
def log_activity_day():
    # 1) Parse + validate payload (robust)
    try:
        current_app.logger.info("REQ CT=%r", request.headers.get("Content-Type"))
        current_app.logger.info("REQ RAW=%r", request.get_data(as_text=True))

        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            try:
                data = json.loads(request.get_data(as_text=True) or "{}")
            except Exception:
                data = {}

        activity_id = int(data["activity_id"])
        day = date.fromisoformat(data["date"])
    except Exception:
        current_app.logger.exception("log_activity_day: bad payload")
        return jsonify(ok=False, error="bad-payload"), 400

    # 2) Ownership check
    activity = Activity.query.filter_by(
        id=activity_id, user_id=current_user.id
    ).first()
    if not activity:
        return jsonify(ok=False, error="not-your-activity"), 403

    # 3) Toggle log
    try:
        existing = ActivityLog.query.filter_by(
            activity_id=activity_id, user_id=current_user.id, date=day
        ).first()

        if existing:
            db.session.delete(existing)
            db.session.commit()
            return jsonify(ok=True, state="removed", activity_id=activity_id)

        new_log = ActivityLog(
            activity_id=activity_id,
            user_id=current_user.id,
            date=day,
        )
        db.session.add(new_log)
        db.session.commit()

        return jsonify(
            ok=True,
            state="added",
            activity_id=activity_id,
            icon=activity.icon_ref,  # for immediate UI render
        )

    except IntegrityError:
        db.session.rollback()
        current_app.logger.exception("log_activity_day: integrity error")
        return jsonify(ok=False, error="db-error"), 500
    except Exception:
        db.session.rollback()
        current_app.logger.exception("log_activity_day: unexpected error")
        return jsonify(ok=False, error="unexpected-error"), 500


@app.post("/activity/<int:activity_id>/delete")
@login_required
def delete_activity(activity_id):
    a = Activity.query.filter_by(id=activity_id, user_id=current_user.id).first()
    if not a:
        return jsonify(ok=False, error="Not found"), 404

    db.session.delete(a)            # ORM cascade removes ActivityLog rows
    db.session.commit()
    return jsonify(ok=True)


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

    # Inner join to avoid orphan rows; all logs will have an Activity
    logs = (
        db.session.query(ActivityLog)
        .join(Activity, Activity.id == ActivityLog.activity_id)
        .filter(
            ActivityLog.user_id == current_user.id,
            ActivityLog.date >= start,
            ActivityLog.date <= end
        )
        .all()
    )

    icons_by_date = {}
    for log in logs:
        act = log.activity  # guaranteed by join
        icons_by_date.setdefault(log.date.isoformat(), []).append({
            "activity_id": log.activity_id,
            "icon_ref": getattr(act, "icon_ref", None),
        })

    logs_json = [
        {
            "date": log.date.isoformat(),
            "activity_id": log.activity_id,
            "icon_ref": getattr(log.activity, "icon_ref", None),
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
