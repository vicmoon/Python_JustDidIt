from flask import Flask, render_template
import datetime as dt
import calendar


app = Flask(__name__)

now = dt.datetime.now()
year = now.year
days_in_year = 366 if calendar.isleap(year) else 365

print(days_in_year)
def get_days():
    days = []
    for i in range(1, days_in_year + 1):
        days.append(i)
    return days
        
    
    
        
@app.route("/")
def home():
    return render_template("index.html", days=get_days())

if (__name__) == "__main__":
    app.run(debug=True)