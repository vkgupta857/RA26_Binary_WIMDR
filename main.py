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
import time
import datetime


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
def date_before_n_days(n):
    tod = datetime.datetime.now()
    d = datetime.timedelta(days = n)
    a = str(tod - d).split('.')[0]
    return(a)

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
            status = req.get(url).text[1]

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


global logged_in
logged_in = 'n'

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
            phone = request.form['phone']
            password = request.form['password']
            login_as=request.form['login']
            if login_as=="Admin":

                data=ndb.child('Managers').get()
                try:
                   p= data.val()[phone]['Password']
                   if password==p:
                       logged_in = 'a'
                       type="Admin"
                       id=data.val()[phone]['Emp_ID']
                       return render_template('Alogin.html',type=type,id=id)
                   else:
                       flash('Invalid Password',category="danger")
                       return redirect(request.url)

                except:
                    flash('Invalid Phone Number',category="danger")
                    return redirect(request.url)

            if login_as=="Manager":

                data=ndb.child('Managers').get()
                try:
                   p= data.val()[phone]['Password']
                   if password==p:
                       logged_in = 'm'
                       type="Manager"
                       name=data.val()[phone]['Name']
                       id=data.val()[phone]['Emp_ID']
                       rating=3
                       return render_template('Mlogin.html',name=name,type=type,id=id,rating=rating)
                   else:
                       flash('Invalid Password',category="danger")
                       return redirect(request.url)

                except:
                    flash('Invalid Phone Number',category="danger")
                    return redirect(request.url)

    return render_template('login.html')

@app.route('/graphs', methods= ['GET', 'POST'])
def graphs():
    if request.method == 'GET':
        p_l=20
        p_m=20
        p_h=60
        p_resolve_on_time=70
        p_resolve_late=30

    if request.method == 'POST':
        state = request.form['state']
        city = request.form['city']
        duration = request.form['duration']

        # duration can be "week", "month", "3_months", "year" or "date"
        # if duration == "date" then start_date and end_date will have values
        if duration == 'custom date':
            start_date = request.form['start date']
            end_date = request.form['end date']
            p_l=20
            p_m=20
            p_h=60
            p_resolve_on_time=70
            p_resolve_late=30

        else:
            if duration == 'week':
                    p_l=20
                    p_m=20
                    p_h=60
                    p_resolve_on_time=70
                    p_resolve_late=30

            elif duration == 'month':
                    p_l=20
                    p_m=20
                    p_h=60
                    p_resolve_on_time=70
                    p_resolve_late=30


            elif duration == '3 months':
                    p_l=20
                    p_m=20
                    p_h=60
                    p_resolve_on_time=70
                    p_resolve_late=30

            elif duration == 'year':
                    p_l=20
                    p_m=20
                    p_h=60
                    p_resolve_on_time=70
                    p_resolve_late=30

        # here we got the pair of dates to run queries

        return render_template('graph.html',p_l=p_l,p_m=p_m,p_h=p_h,p_resolve_on_time=p_resolve_on_time,p_resolve_late=p_resolve_late)
    return render_template('graph.html',p_l=p_l,p_m=p_m,p_h=p_h,p_resolve_on_time=p_resolve_on_time,p_resolve_late=p_resolve_late)




###############################################
# API Routes Section for Android app and AJAX requests
###############################################


# api for adding report data to database from android
@app.route('/add',methods=['GET','POST'])
def add():
    if request.method == 'POST':
        row = request.json
        return(thedb.add_row(row))


# api for adding data from csv to database
@app.route('/csvtodb',methods=['GET'])
def csvtodb():
    r = thedb.add_csv_data()
    return(r)

@app.route('/check',methods=['GET'])
def check():
    r = thedb.check()
    d = {'label':[], 'count':[]}
    for row in r:
        d['label'].append(row[0])
        d['count'].append(row[1])
    return(d)

# Route for reports
@app.route('/reports', methods= ['GET', 'POST'])
def reports():
    if request.method == 'POST':
        state = request.form['state']
        district = request.form['city']
        duration = request.form['duration']
        start_date = None
        end_date = None

        # duration can be "week", "month", "3_months", "year" or "date"
        # if duration == "date" then start_date and end_date will have values
        if duration == 'date':
            start_date = request.form['startDate']
            end_date = request.form['endDate']
        else:
            if duration == 'week':
                end_date = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime'].split('T')[0]
                start_date = date_before_n_days(7)
            elif duration == 'month':
                end_date = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime'].split('T')[0]
                start_date = date_before_n_days(30)
            elif duration == '3_months':
                end_date = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime'].split('T')[0]
                start_date = date_before_n_days(90)
            elif duration == 'year':
                end_date = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime'].split('T')[0]
                start_date = date_before_n_days(365)
        # here we got the pair of dates to run queries

        if state == 'all':
            # when no state is chosen
            # call function to select all records between start_date and end_date
            m = thedb.MainQuery(state='all', district='all', start_date=start_date, end_date=end_date)
        else:
            # when a state is chosen
            if district == 'all':
                # when no district is chosen
                m = thedb.MainQuery(state=state, district='all', start_date=start_date, end_date=end_date)
                # call function to select all records in mentioned state
                # and between start_date and end_date
            else:
                # when district is chosen
                m = thedb.MainQuery(state=state, district=district, start_date=start_date, end_date=end_date)
                # call function to select all records in mentioned state and district
                # and between start_date and end_date

        print(m)

        response = {}
        response['state'] = state
        response['city'] = district
        response['duration'] = duration
        response['startDate'] = start_date
        response['endDate'] = end_date
        return json.dumps(response)

    return render_template('reports.html')

###########
# Run App
###########

if __name__ == '__main__':
   app.run()