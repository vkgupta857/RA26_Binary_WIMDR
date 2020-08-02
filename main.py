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
#app.config['UPLOAD_FOLDER'] = '/tmp/'

# for local
app.config['UPLOAD_FOLDER'] = 'static/uploads'


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

# function for creating Heatmap with time
def create_heatmap_with_time(data, time_index, place):
    # takes data and time_index as input
    m = folium.Map(
        data[0][0],
        tiles='stamentoner',
        zoom_start={'state':6, 'district':13}[place])

    hm = plugins.HeatMapWithTime(
        data,
        index=time_index,
        auto_play=False,
        max_opacity=0.3
    )
    
    hm.add_to(m)
    m.save('templates/heatmap-time.html')
    return('heatmap-time.html')

# function for creating heatmap
def create_heatmap(data,place):
    try:
        location = res[0]
        zoom_start={'state':6, 'district':13}[place]
    except:
        location = [27.44,  77.67]
        zoom_start = 6
    map = folium.Map(zoom_start=zoom_start,
                     location=location, 
                     control_scale=True)
    folium.plugins.HeatMap(data, radius=8, max_zoom=13).add_to(map)
    map.save('templates/heatmap1.html')
    return('heatmap1.html')
    
# function to create cluster-map
def create_cluster_map(res):
    # function to create cluster map only for district
    colorCode = {'H':'red', 'M':'orange', 'L':'green'}
    map = folium.Map(zoom_start=10,location=[19.05,  72.85], control_scale=True)
    map = folium.plugins.MarkerCluster().add_to(map)
    for row in res:
        color = colorCode[row[1]]
        popupmsg='{} {}'.format({'L':'Low','M':'Medium','H':'High'}[row[1]],str(row[0]))
        folium.Marker([float(row[2]), float(row[3])],popup=popupmsg,icon=folium.Icon(color=color, icon='info-sign')).add_to(map)
    map.save('templates/cluster_map_city.html')
    return('cluster_map_city.html')

# fucntion to get a date before n days of current date
def date_before_n_days(n):
    dt = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime']
    dt = dt.replace('T',' ').split('.')[0]
    tod = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    d = datetime.timedelta(days = n)
    a = str(tod - d).split('.')[0]
    a = a.split(' ')[0]
    return(a)

# function to get the unique filename for each report
# to neglect the chances of overwriting an image in database
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
    
def get_points(city):
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
    return report


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
            pathlocal= 'static/uploads/'+'image.jpg'
            #pathlocal = '/tmp/image.jpg'

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

            return render_template('uploaded_file.html',filename=filename, label={'L':'Low','M':'Medium','H':'High'}[status])

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

                data=ndb.child('Admin').get()
                try:
                   p= data.val()['Password']
                   if password==p:
                       logged_in = 'a'
                       name=data.val()['Name']
                       type="Admin"
                       id='KPUtGo75965'
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
                   p= data.val()[phone]['Password']
                   if password==p:
                        logged_in = 'm'
                        name=data.val()[phone]['Name']
                        id=data.val()[phone]['Emp_ID']
                        state=data.val()[phone]['State']
                        type="Manager"
                        city=data.val()[phone]['District']
                    
                        rating= thedb.get_emp_rating(city)
                        time="24 hrs per report"
                        return render_template('Mlogin.html',name=name,type=type,id=id,rating=rating,city=city,time=time,state=state)
                   
                  
                   else:
                       flash('Invalid Password',category="danger")
                       return redirect(request.url)

                except:
                    flash('Invalid Phone Number',category="danger")
                    return redirect(request.url)

    return render_template('login.html')



@app.route('/map', methods=['GET', 'POST'])
def map():
    city = request.args.get('city')
    state = request.args.get('state')
    if request.method == 'POST':
        city = request.form['city']
        state = request.form['state']
        report = get_points(city)
        response = {}
        response['points'] = report
        return response

    return render_template('map.html',city=city,state=state)

@app.route('/clustermap', methods= ['GET', 'POST'])
def clustermap():
    return render_template('clustermap.html')

@app.route('/heatmap', methods= ['GET', 'POST'])
def heatmap():
    return render_template('heatrmap.html')

@app.route('/ClustermapM', methods=['GET', 'POST'])
def ClustermapM():
    city = request.args.get('city')
    state = request.args.get('state')
    dt = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime']
    dt = dt.replace('T',' ').split('.')[0]
    end_date=dt.split(' ')[0]
    start_date = date_before_n_days(30)
    qobj = thedb.MainQuery(state=state, district=city, start_date=start_date, end_date=end_date)
    res=qobj.get_clustermap_data()
    filename=create_cluster_map(res)
    return render_template(filename)


@app.route('/graphs', methods= ['GET', 'POST'])
def graphs():
    if request.method == 'GET':
        # 'qobj' stands for query-object
        qobj = thedb.MainQuery()

        #data for pie charts
        count = qobj.get_label_count()
        c_l= count['L']
        c_m= count['M']
        c_h= count['H']
        count = qobj.get_resolved_count()
        c_resolve_on_time= count['1']
        c_resolve_late= count['2']
        c_pending=20

        #data for top 5 cities
        #clean,dirty=

        params={'c_l':c_l,'c_m':c_m,'c_h':c_h,'c_resolve_on_time':c_resolve_on_time,'c_resolve_late':c_resolve_late,'c_pending':c_pending}

    if request.method == 'POST':
        state = request.form['state']
        city = request.form['city']
        duration = request.form['duration']
        print(state,district,duration)
        # duration can be "week", "month", "3_months", "year" or "date"
        # if duration == "date" then start_date and end_date will have values
        
        if duration == 'date':
            start_date = request.form['start date']
            end_date = request.form['end date']
            qobj = thedb.MainQuery(state,city,start_date,end_date)

        else:
            if duration == 'week':
                dt = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime']
                dt = dt.replace('T',' ').split('.')[0]
                end_date=dt.split(' ')[0]
                start_date = date_before_n_days(7)
                qobj = thedb.MainQuery(state,city,start_date,end_date)

            elif duration == 'month':
                dt = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime']
                dt = dt.replace('T',' ').split('.')[0]
                end_date=dt.split(' ')[0]
                start_date = date_before_n_days(30)
                qobj = thedb.MainQuery(state,city,start_date,end_date)

            elif duration == '3 months':
                dt = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime']
                dt = dt.replace('T',' ').split('.')[0]
                end_date=dt.split(' ')[0]
                start_date = date_before_n_days(90)
                qobj = thedb.MainQuery(state,city,start_date,end_date)

            elif duration == 'year':
                dt = json.loads(req.get('http://worldtimeapi.org/api/timezone/Asia/Kolkata').text)['datetime']
                dt = dt.replace('T',' ').split('.')[0]
                end_date=dt.split(' ')[0]
                start_date = date_before_n_days(365)
                qobj = thedb.MainQuery(state,city,start_date,end_date)

            elif duration == 'all':
                qobj = thedb.MainQuery(state,city)

        #data for bar graph
        daily,weekly=qobj.get_barplot_data()
        response={}
        response['daily']=daily
        response['weekly']=weekly

        #data for pie charts
        count = qobj.get_label_count()
        print("Count for labels",count)
        if(not (count['L'] or count['L'] or count['L'])):
            print("No data")
        c_l= count['L']
        c_m= count['M']
        c_h= count['H']
        count = qobj.get_resolved_count()
        print("Count for labels",count)
        c_resolve_on_time= count['1']
        c_resolve_late= count['2']
        c_pending=20

        # Commenting params. It has no use for now - Vinod
        # params={'c_l':c_l,'c_m':c_m,'c_h':c_h,'c_resolve_on_time':c_resolve_on_time,'c_resolve_late':c_resolve_late,'c_pending':c_pending}
        response['c_l'] = c_l
        response['c_m'] = c_m
        response['c_h'] = c_h
        response['c_resolve_on_time'] = c_resolve_on_time
        response['c_resolve_late'] = c_resolve_late
        return response

    return render_template('graphs.html',params=params)


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


###########
# Run App
###########

if __name__ == '__main__':
   app.run()
