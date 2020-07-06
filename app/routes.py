import os
import json
from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename

from app import app

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        place = request.form['place']
        print(place)
        lat = request.form['latitude']
        lng = request.form['longitude']
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
            flash(place+lat+lng, category="primary")
            return render_template('uploaded_file.html',filename=filename)

        else:
            flash("Invalid file type", category="danger")
            return redirect(request.url)
    # for GET request
    return render_template('upload.html')

@app.route('/update')
def update():
    return render_template('update.html')

@app.route('/view')
def view():
    return render_template('view.html')

@app.route('/week')
def week():
    return render_template('week.html')

@app.route('/piechart')
def piechart():
    return render_template('piechart.html')


def allowed_file(filename):
    ALLOWED_EXTENSIONS = ['jpg', 'png']
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/test', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        print(file)
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return render_template('uploaded_file.html',filename=filename)
        else:
            flash("Invalid file")
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


##############################################
# API Section starts here
# -----------
# API is for Android app and AJAX requests
#############

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
