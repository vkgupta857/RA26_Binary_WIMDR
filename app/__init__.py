from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from config import Config

app = Flask(__name__)
app.config.from_object(Config)

app.config['UPLOAD_FOLDER'] = 'app/static/uploads'

db = SQLAlchemy(app)
migrate = Migrate(app,db)

# import required at this place
from app import routes
