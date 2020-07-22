import os
import json
from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
# import waste_classification as wc
from datetime import datetime
# for getting state and district
import reverse_geocoder as rg
# for accessing database
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import urllib.request
import random
import employee_id
import requests as req
# for database connectivity
import sqlalchemy
#for connecting with firestorage
import pyrebase


# Remember - storing secrets in plaintext is potentially unsafe. Consider using
# something like https://cloud.google.com/kms/ to help keep secrets secret.
db_user = os.environ.get("DB_USER")
db_pass = os.environ.get("DB_PASS")
db_name = os.environ.get("DB_NAME")
cloud_sql_connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME")

# [START cloud_sql_mysql_sqlalchemy_create]
# The SQLAlchemy engine will help manage interactions, including automatically
# managing a pool of connections to your database
db = sqlalchemy.create_engine(
    # Equivalent URL:
    # mysql+pymysql://<db_user>:<db_pass>@/<db_name>?unix_socket=/cloudsql/<cloud_sql_instance_name>
    sqlalchemy.engine.url.URL(
        drivername="mysql+pymysql",
        username=db_user,
        password=db_pass,
        database=db_name,
        query={"unix_socket": "/cloudsql/{}".format(cloud_sql_connection_name)},
    ),
    # ... Specify additional properties here.
    # [START_EXCLUDE]
    # [START cloud_sql_mysql_sqlalchemy_limit]
    # Pool size is the maximum number of permanent connections to keep.
    pool_size=5,
    # Temporarily exceeds the set pool_size if no connections are available.
    max_overflow=2,
    # The total number of concurrent connections for your application will be
    # a total of pool_size and max_overflow.
    # [END cloud_sql_mysql_sqlalchemy_limit]
    # [START cloud_sql_mysql_sqlalchemy_backoff]
    # SQLAlchemy automatically uses delays between failed connection attempts,
    # but provides no arguments for configuration.
    # [END cloud_sql_mysql_sqlalchemy_backoff]
    # [START cloud_sql_mysql_sqlalchemy_timeout]
    # 'pool_timeout' is the maximum number of seconds to wait when retrieving a
    # new connection from the pool. After the specified amount of time, an
    # exception will be thrown.
    pool_timeout=30,  # 30 seconds
    # [END cloud_sql_mysql_sqlalchemy_timeout]
    # [START cloud_sql_mysql_sqlalchemy_lifetime]
    # 'pool_recycle' is the maximum number of seconds a connection can persist.
    # Connections that live longer than the specified amount of time will be
    # reestablished
    pool_recycle=1800,  # 30 minutes
    # [END cloud_sql_mysql_sqlalchemy_lifetime]
    # [END_EXCLUDE]
)
# [END cloud_sql_mysql_sqlalchemy_create]


app = Flask(__name__)

##################
# Config Section
##################

app.config['SECRET_KEY'] = "MySecretKeyDontCopy"
app.config['UPLOAD_FOLDER'] = 'static/uploads'


cred = credentials.Certificate('SIH-Realtime-DB.json')
firebase_admin.initialize_app(cred, {'databaseURL':'https://sih-db-3b091.firebaseio.com/'})

config={
    "apiKey": "AIzaSyBumH3t0dgqUQfNRx0lhZdrp4UcA0s6r7o",
    "authDomain": "sih-db-3b091.firebaseapp.com",
    "databaseURL": "https://sih-db-3b091.firebaseio.com",
    "projectId": "sih-db-3b091",
    "storageBucket": "sih-db-3b091.appspot.com",
    "messagingSenderId": "826516287205",
    "appId": "1:826516287205:web:7421a9ecfb7ac8e7b02e0c"

}

firebase=pyrebase.initialize_app(config)
storage= firebase.storage()


######################
# App Routes Section
######################
def get_date_time():
    d,t = str(datetime.now()).split(' ')
    d = d.split('-')
    d = d[2]+'/'+d[1]+'/'+d[0]
    t = t.split(':')
    t = t[0]+':'+t[1]+':'+t[2][0:2]
    return d,t


def get_place(lat,lng):
    result = rg.search((lat,lng))
    state = result[0]['admin1']
    district = result[0]['admin2']
    return district,state


def allowed_file(filename):
    '''
    Function to check file types
    '''
    ALLOWED_EXTENSIONS = ['jpg', 'png']
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET','POST'])
def upload():
    # If request method is POST
    if request.method == 'POST':
        lat = request.form['latitude']
        lng = request.form['longitude']

        # Check if location is missing
        if lat == "" and lng == "":
            flash("Location missing! Image cannot be uploaded without location.", category="danger")
            return redirect(request.url)

        # check if the post request has the image
        if 'image' not in request.files:
            flash('No file uploaded')
            return redirect(request.url)

        file = request.files['image']

        # if request with no file
        if file.filename == '':
            flash('No image attached. Please attach an image of waste.',category="danger")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            pathoncloud='images/'+filename
            pathlocal= 'static/uploads/'+filename
            storage.child(pathoncloud).put(pathlocal)

            flash("Image uploaded successfully", category="success")

            #classification
            url = 'https://waste-classification-api.el.r.appspot.com/' + filename
            status = req.get(url).text

            # getting date and time
            d,t = get_date_time()

            # getting state and district
            district, state = get_place(lat, lng)

            # gettig emp_id
            try:
                emp_id = employee_id.emp_id[state][district]
            except:
                emp_id = 0

            # adding report to the database
            data = {'Report_No' : str(random.randint(10**4,10**5)),
                    'State' : str(state),
                    'District' : str(district),
                    'Lattitude' : str(lat),
                    'Longitude' : str(lng),
                    'Report_Date' : str(d),
                    'Report_Time' : str(t),
                    'Status' : str(status),
                    'Pick_Date' : str(0),
                    'Pick_Time' : str(0),
                    'Resolved' : str(0),
                    'Emp_ID' : str(emp_id),
                    'Image' : str(filename)}

            ref = db.reference('Pending_Reports')
            ref.push(data)

            return render_template('uploaded_file.html',filename=filename, label=status)

        else:
            flash("Invalid file type", category="danger")
            return redirect(request.url)

    # If request method is other than POST e.g. GET
    return render_template('upload.html')

@app.route('/view')
def view():
    return render_template('view.html')

@app.route('/statistics')
def statistics():
    return render_template('statistics.html')

###############################################
# API Routes Section for Android app and AJAX requests
###############################################

@app.route('/api/json')
def api_json():
    response = {}
    response['data'] = ['1','2','3']
    return json.dumps(response)

@app.route('/api/report/weekly')
def api_report_weekly():
    response = {}
    response['data'] = ['1','2','3']
    return json.dumps(response)

###########
# Run App
###########

if __name__ == '__main__':
   app.run()
