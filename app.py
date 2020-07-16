import os
import json
from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import waste_classification as wc
from datetime import datetime
# for getting state and district
import reverse_geocoder as rg
# for accessing database
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

import random
import employee_id

app = Flask(__name__)

##################
# Config Section
##################

app.config['SECRET_KEY'] = "MySecretKeyDontCopy"
app.config['UPLOAD_FOLDER'] = 'static/uploads'


cred = credentials.Certificate('SIH-Realtime-DB.json')
firebase_admin.initialize_app(cred, {'databaseURL':'https://sih-db-3b091.firebaseio.com/'})


######################
# App Routes Section
######################
def get_date_time():
    d,t = str(datetime.now()).split(' ')
    d = d.split('-')
    d = d[2]+'/'+d[1]+'/'+d[0]
    t = t.split(':')
    t = t[0]+':'+t[1]
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
            flash("Image uploaded successfully", category="success")
            
            #classification
            label = wc.predict('static/uploads/'+filename)
            # getting waste status
            status = ['Low','Medium','High'][label]
            
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
            data = {'Report No' : str(random.randint(10**4,10**5)),
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
            
            ref = db.reference('New_Reports')
            ref.push(data)
            
            return render_template('uploaded_file.html',filename=filename, label=label)

        else:
            flash("Invalid file type", category="danger")
            return redirect(request.url)

    # If request method is other than POST e.g. GET
    return render_template('upload.html')

@app.route('/update')
def update():
    return render_template('update.html')

@app.route('/view')
def view():
    return render_template('view.html')

'''
@app.route('/statistics')
def view():
    return render_template('statistics.html')
'''

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
