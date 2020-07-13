from flask import Flask, render_template, request, session, redirect , jsonify, make_response,url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
#from werkzeug.utils import secure_filename
import os
#UPLOAD_FOLDER = os.path.join('static','Image')

app = Flask(__name__)
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:@localhost/wastemanagement"
db = SQLAlchemy(app)


class Report(db.Model):
    Report_No = db.Column(db.Integer, primary_key=True)
    Image = db.Column(db.String(60), nullable=True)
    Report_Date = db.Column(db.String(10), nullable=True)
    Report_Time = db.Column(db.String(8), nullable=True)
    Status = db.Column(db.String(6), nullable=True)
    Longitude = db.Column(db.String(15), nullable=True)
    Lattitude = db.Column(db.String(15), nullable=True)
    Area=db.Column(db.String(20), nullable=True)


class Resolve(db.Model):
    Report_No = db.Column(db.Integer , primary_key=True)
    Emp_Id = db.Column(db.Integer , nullable=True)
    Pick_Time = db.Column(db.String(8), nullable=True)
    Pick_Date = db.Column(db.String(10), nullable=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/upload")
def upload():
    return render_template("upload.html")

@app.route("/update")
def update():
    return render_template("update.html")

@app.route("/view")
def view():
    a=1
    b=2
    c=3
    d=4
    e=5
    return render_template("view.html",a=a,b=b,c=c,d=d,e=e)

@app.route("/pie",methods=['GET','POST'])
def pie():
        per_r=30
        per_nr=70
        per_l=30
        per_m=30
        per_h=40

        return render_template("piechart.html",per_r=per_r,per_nr=per_nr,per_l=per_l,per_m=per_m,per_h=per_h)




@app.route("/piee",methods=['GET','POST'])
def piee():
    if request.method == 'POST':

        loc = str((request.form.get('menu')))
        loc.lower()
    if loc=="ranjhi":
        per_r=40
        per_nr=60
        per_l=20
        per_m=60
        per_h=20

        return render_template("pichart.html",per_r=per_r,per_nr=per_nr,per_l=per_l,per_m=per_m,per_h=per_h)

    if loc=="gol bazar":
        per_r=5
        per_nr=6
        per_l=5
        per_m=6
        per_h=7

        return render_template("pichart.html",per_r=per_r,per_nr=per_nr,per_l=per_l,per_m=per_m,per_h=per_h)

    if loc=="sadar":
        per_r=5
        per_nr=6
        per_l=5
        per_m=6
        per_h=7

        return render_template("pichart.html",per_r=per_r,per_nr=per_nr,per_l=per_l,per_m=per_m,per_h=per_h)

    if loc=="ghamapur":
        per_r=5
        per_nr=6
        per_l=5
        per_m=6
        per_h=7

        return render_template("pichart.html",per_r=per_r,per_nr=per_nr,per_l=per_l,per_m=per_m,per_h=per_h)



@app.route("/submit", methods=['POST'])
def submit():

    f = request.files['fileToUpload']
    a = str(request.form.get('menu'))
    s= "Low"
    entry = Report(Image=f.filename ,Report_Date= datetime.now(),Report_Time= datetime.now(), Status= s ,Longitude=5, Lattitude=6,Area=a )
    db.session.add(entry)
    db.session.commit()
    return render_template("upload.html")

@app.route("/confrim", methods=['POST'])
def confrim():
    x= request.form.get('report')
    y= request.form.get('id')
    entry = Resolve(Report_No = x , Emp_Id= y ,Pick_Time= datetime.now(),  Pick_Date= datetime.now())
    db.session.add(entry)
    db.session.commit()
    return render_template("update.html")

@app.route("/views", methods=['GET','POST'])
def views():

    if request.method == 'POST':

        loc = str((request.form.get('menu')))
        loc.lower()


    if loc=="ranjhi":
        f=os.path.join(app.config['UPLOAD_FOLDER'],'ranjhipic1.png')
        return render_template('view.html',image=f)

    if loc=="gokalpur":
        f=os.path.join(app.config['UPLOAD_FOLDER'],'gokalpurmap1.png')
        return render_template('view.html',image=f)

    if loc=="khamaria":
        f=os.path.join(app.config['UPLOAD_FOLDER'],'khamaria.png')
        return render_template('view.html',image=f)

    if loc=="vehicle":
        f=os.path.join(app.config['UPLOAD_FOLDER'],'vehiclefactorymap1.png')
        return render_template('view.html',image=f)

    if loc=="select":
        f=os.path.join(app.config['UPLOAD_FOLDER'],'fullmapnew.png')
        return render_template('view.html',image=f)



app.run(debug=True)
