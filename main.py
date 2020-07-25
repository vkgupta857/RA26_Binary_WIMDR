import os
import json
from flask import Flask, render_template, request, flash, redirect
from werkzeug.utils import secure_filename
# import waste_classification as wc
# for getting state and district
import reverse_geocoder as rg
# for accessing database
# import firebase_admin
# from firebase_admin import credentials
# from firebase_admin import db
import random
import employee_id
# for database connectivity
import sqlalchemy
# for connecting with firestorage
import pyrebase
import the_database as thedb
import requests as req
import json
import string


app = Flask(__name__)

##################
# Config Section
##################

app.config['SECRET_KEY'] = "MySecretKeyDontCopy"
# Temporarily file can be uploaded in '/tmp' folder in GCP
app.config['UPLOAD_FOLDER'] = '/tmp/'

# for local
# app.config['UPLOAD_FOLDER'] = 'static/uploads'


# cred = credentials.Certificate('SIH-Realtime-DB.json')
# firebase_admin.initialize_app(cred, {'databaseURL':'https://sih-db-3b091.firebaseio.com/'})

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
ndb = firebase.database()


######################
# App Routes Section
######################
def get_filename():
    length = 5
    letters = string.ascii_letters
    result =  'image_'+''.join(random.choice(letters) for i in range(length))+'.jpg'
    return(result)


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
            filename = get_filename()
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'image.jpg'))
            pathoncloud='images/'+filename
            #pathlocal= 'static/uploads/'+filename
            pathlocal = '/tmp/image.jpg'

            storage.child(pathoncloud).put(pathlocal)

            flash("Image uploaded successfully", category="success")

            #classification
            url = 'https://waste-classification-api.el.r.appspot.com/' + filename
            status = req.get(url).text[0]

            # getting date and time
            dt = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime']
            dt = dt.replace('T',' ').split('.')[0]

            # getting state and district
            district, state = get_place(lat, lng)

            # gettig emp_id
            try:
                emp_ID = employee_id.emp_id[state][district]
            except:
                emp_ID = 0

            # adding report to the database
            data = {'state' : str(state),
                    'district' : str(district),
                    'lattitude' : str(lat),
                    'longitude' : str(lng),
                    'report_time' : str(dt),
                    'status' : str(status),
                    'pick_Time' : str(0),
                    'resolved' : str(0),
                    'emp_ID' : str(emp_ID),
                    'filename' : str(filename)}

            # ref = db.reference('Pending_Reports')
            # ref.push(data)
            ndb.child('Pending_Reports').push(data)

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

global logged_in = 'n'
@app.route('/admin',methods=['GET','POST'])
def admin():
    if request.method == 'POST':
            phone = request.form['phone']
            password = request.form['password']
            data=ndb.child('Managers').get()
            try:
               p= data.val()([phone]['Password'])
               if password==p:
                   global logged_in='a'
                   return render_template('admin_login.html')
               flash('Invalid Password',category="danger")
               return redirect(request.url)

            except:
                flash('Invalid Phone Number',category="danger")
                return redirect(request.url)

    return render_template('admin.html')

@app.route('/manager',methods=['GET','POST'])
def manager():

    if request.method == 'POST':
            phone = request.form['phone']
            password = request.form['password']
            data=ndb.child('Managers').get()
            try:
               p= data.val()([phone]['Password'])
               if password==p:
                   global logged_in='m'
                   return render_template('manager_login.html')
               flash('Invalid Password',category="danger")
               return redirect(request.url)

            except:
                flash('Invalid Phone Number',category="danger")
                return redirect(request.url)

    return render_template('manager.html')


###############################################
# API Routes Section for Android app and AJAX requests
###############################################


# api for adding report data to database from android
@app.route('/add',methods=['GET','POST'])
def add():
    if request.method == 'POST':
        row = request.json
        return(thedb.add_row(row))
    

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
