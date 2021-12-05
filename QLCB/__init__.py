from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_admin import Admin
import cloudinary

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:26042001@localhost/qlcbdb?charset=utf8mb4"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config["MIN_FLIGHT_TIME"] = 30
app.config["MAX_STOPOVER_PER_FLIGHT"] = 2
app.config["MIN_TIME_STOPOVER_PER_FLIGHT"] = 10
app.config["MAX_TIME_STOPOVER_PER_FLIGHT"] = 20
app.config["MAX_DATE_ALLOWED_BOOKING_BEFORE_TAKEOFF"] = 1
app.config["PAGE_SIZE"] = 6
app.secret_key = 'super secret key'

db = SQLAlchemy(app)
login = LoginManager(app=app)

admin = Admin(app=app, name='FLY', template_mode='bootstrap4')

cloudinary.config(
  cloud_name="djudnibwn",
  api_key="554142242719516",
  api_secret="-qnH-Pc6ibrKyjd9FODdGgI-Q3s"
)
