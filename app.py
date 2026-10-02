from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # убирает warning
app.config['SECRET_KEY'] = 'dev-secret-key-change-me'

db = SQLAlchemy(app)
migrate = Migrate(app, db)