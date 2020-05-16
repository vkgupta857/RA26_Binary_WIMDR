from flask import Flask

app = Flask(__name__)

# import required at this place
from app import routes

app.run(debug=True)