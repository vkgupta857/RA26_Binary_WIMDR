from flask import Flask, render_template
from app import app

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload():
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
