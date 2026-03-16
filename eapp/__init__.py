from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary

app = Flask(__name__)
app.secret_key = 'topupsystem-16032026'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Abcd123,@localhost/salecarddb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app=app)
login = LoginManager(app=app)

cloudinary.config(cloud_name='dfgicbdji',
api_key='124197697555968',
api_secret='45n1Ut4C5xt4bdquewTAzc9dcB8')