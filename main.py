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

# while deployment uncomment below line
#import the_database as thedb
# while using locally uncomment below line
import the_database_local as thedb

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
    dt = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime']
    dt = dt.replace('T',' ').split('.')[0]
    tod = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    d = datetime.timedelta(days = n)
    a = str(tod - d).split('.')[0]
    a = a.split(' ')[0]
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

def islate(now, report_time):
    now = datetime.datetime.strptime(now, '%Y-%m-%d %H:%M:%S')
    report_time = datetime.datetime.strptime(report_time, '%Y-%m-%d %H:%M:%S')
    diff = now - report_time
    if diff.days > 0:
        return('Late')
    else:
        return('Ontime')

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
                       name=data.val()[phone]['Name']
                       type="Admin"
                       id=data.val()[phone]['Emp_ID']
                       return render_template('Alogin.html',name=name,type=type,id=id)
                   else:
                       flash('Invalid Password',category="danger")
                       return redirect(request.url)

                except:
                    flash('Invalid Phone Number',category="danger")
                    return redirect(request.url)

            if login_as=="Manager":

                data=ndb.child('Managers').get()
                try:

                   if password==p:
                        logged_in = 'm'
                        name=data.val()[phone]['Name']
                        id=data.val()[phone]['Emp_ID']
                        rating=3
                        type="Manager"
                        city=data.val()[phone]['District']
                        l=[]
                        report=[]
                        r=ndb.child('Pending_Reports').get()
                        for i in r.each():
                            if city==i.val()['district']:
                                l.append(i.key())
                        for j in l:
                            d={}
                            d.__setitem__('lattitude', r.val()[j]['lattitude'])
                            d.__setitem__('longitude', r.val()[j]['longitude'])
                            d.__setitem__('status', r.val()[j]['status'])
                            d.__setitem__('report_time', r.val()[j]['report_time'])
                            report.append(d)

                            for k in report:
                                now = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime']
                                now = now.replace('T',' ').split('.')[0]
                                status=islate(now,k['report_time'])
                                if status=="Late":
                                    k['status']=status

                        return render_template('Mlogin.html',name=name,type=type,id=id,rating=rating,city=city,points=report)
                   else:
                       flash('Invalid Password',category="danger")
                       return redirect(request.url)

                except:
                    flash('Invalid Phone Number',category="danger")
                    return redirect(request.url)

    return render_template('login.html')



@app.route('/map', methods=['GET', 'POST'])
def map():
    if request.method == 'POST':
        response = {}
        points = [{
            "lat": 23.1347137792272,
            "lng": 79.9275922311487,
            "waste_type": "high"
        },
        {
            "lat": 23.1343797088188,
            "lng": 79.9523614706786,
            "waste_type": 'alert'
        }]
        response['points'] = points
        return response

    return render_template('map.html')

@app.route('/graphs', methods= ['GET', 'POST'])
def graphs():
    if request.method == 'GET':
        # 'qobj' stands for query-object
        qobj = thedb.MainQuery()
        count = qobj.get_label_count()
        p_l= count['L']
        p_m= count['M']
        p_h= count['H']
        # converting count in percentage
        s = p_l+p_m+p_h
        p_l,p_m,p_h = (p_l*100)/s, (p_m*100)/s, (p_h*100)/s
        count = qobj.get_resolved_count()
        p_resolve_on_time= count['1']
        p_resolve_late= count['2']
        params={'p_l':p_l,'p_m':p_m,'p_h':p_h,'p_resolve_on_time':p_resolve_on_time,'p_resolve_late':p_resolve_late}

    if request.method == 'POST':
        state = request.form['state']
        city = request.form['city']
        duration = request.form['duration']

        # duration can be "week", "month", "3_months", "year" or "date"
        # if duration == "date" then start_date and end_date will have values
        if duration == 'custom date':
            start_date = request.form['start date']
            end_date = request.form['end date']
            qobj = thedb.MainQuery(state,city,start_date,end_date)
            count = qobj.get_label_count()
            p_l= count['L']
            p_m= count['M']
            p_h= count['H']
            # converting count in percentage
            s = p_l+p_m+p_h
            p_l,p_m,p_h = (p_l*100)/s, (p_m*100)/s, (p_h*100)/s
            count = qobj.get_resolved_count()
            p_resolve_on_time= count['1']
            p_resolve_late= count['2']
            params={'p_l':p_l,'p_m':p_m,'p_h':p_h,'p_resolve_on_time':p_resolve_on_time,'p_resolve_late':p_resolve_late}


        else:
            if duration == 'week':
                dt = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime']
                dt = dt.replace('T',' ').split('.')[0]
                end_date=dt.split('')[0]
                start_date = date_before_n_days(7)
                qobj = thedb.MainQuery(state,city,start_date,end_date)
                count = qobj.get_label_count()
                p_l= count['L']
                p_m= count['M']
                p_h= count['H']
                # converting count in percentage
                s = p_l+p_m+p_h
                p_l,p_m,p_h = (p_l*100)/s, (p_m*100)/s, (p_h*100)/s
                count = qobj.get_resolved_count()
                p_resolve_on_time= count['1']
                p_resolve_late= count['2']
                params={'p_l':p_l,'p_m':p_m,'p_h':p_h,'p_resolve_on_time':p_resolve_on_time,'p_resolve_late':p_resolve_late}



            elif duration == 'month':
                dt = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime']
                dt = dt.replace('T',' ').split('.')[0]
                end_date=dt.split('')[0]
                start_date = date_before_n_days(30)
                qobj = thedb.MainQuery(state,city,start_date,end_date)
                count = qobj.get_label_count()
                p_l= count['L']
                p_m= count['M']
                p_h= count['H']
                # converting count in percentage
                s = p_l+p_m+p_h
                p_l,p_m,p_h = (p_l*100)/s, (p_m*100)/s, (p_h*100)/s
                count = qobj.get_resolved_count()
                p_resolve_on_time= count['1']
                p_resolve_late= count['2']
                params={'p_l':p_l,'p_m':p_m,'p_h':p_h,'p_resolve_on_time':p_resolve_on_time,'p_resolve_late':p_resolve_late}



            elif duration == '3 months':
                dt = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime']
                dt = dt.replace('T',' ').split('.')[0]
                end_date=dt.split('')[0]
                start_date = date_before_n_days(90)
                qobj = thedb.MainQuery(state,city,start_date,end_date)
                count = qobj.get_label_count()
                p_l= count['L']
                p_m= count['M']
                p_h= count['H']
                # converting count in percentage
                s = p_l+p_m+p_h
                p_l,p_m,p_h = (p_l*100)/s, (p_m*100)/s, (p_h*100)/s
                count = qobj.get_resolved_count()
                p_resolve_on_time= count['1']
                p_resolve_late= count['2']
                params={'p_l':p_l,'p_m':p_m,'p_h':p_h,'p_resolve_on_time':p_resolve_on_time,'p_resolve_late':p_resolve_late}


            elif duration == 'year':
                dt = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime']
                dt = dt.replace('T',' ').split('.')[0]
                end_date=dt.split('')[0]
                start_date = date_before_n_days(365)
                qobj = thedb.MainQuery(state,city,start_date,end_date)
                count = qobj.get_label_count()
                p_l= count['L']
                p_m= count['M']
                p_h= count['H']
                # converting count in percentage
                s = p_l+p_m+p_h
                p_l,p_m,p_h = (p_l*100)/s, (p_m*100)/s, (p_h*100)/s
                count = qobj.get_resolved_count()
                p_resolve_on_time= count['1']
                p_resolve_late= count['2']
                params={'p_l':p_l,'p_m':p_m,'p_h':p_h,'p_resolve_on_time':p_resolve_on_time,'p_resolve_late':p_resolve_late}

        return render_template('graph.html',params=params)
    return render_template('graph.html',params=params)





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
'''
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
'''

###########
# Run App
###########

if __name__ == '__main__':
   app.run()
