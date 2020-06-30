from flask import Flask, render_template, request, session, redirect , jsonify, make_response, url_for
from datetime import datetime, date
import pandas as pd
import numpy as np
import os
from flask_ngrok import run_with_ngrok
from fastai.vision import *


def dweek():
    rep = pd.read_csv('reports.csv')

    low = []
    high = []
    mid = []

    for i in range(rep.shape[0]):
        if rep['Status'][i] == 'Low':
            l = [rep['Lattitude'][i],rep['Longitude'][i]]
            low.append(l)

        elif rep['Status'][i] == 'Medium':
            l = [rep['Lattitude'][i],rep['Longitude'][i]]
            mid.append(l)

        elif rep['Status'][i] == 'High':
            l = [rep['Lattitude'][i],rep['Longitude'][i]]
            high.append(l)
    return low,mid,high


def data_query(pro):
    rep = pd.read_csv('reports.csv')
    res = pd.read_csv('resolve.csv')

    if pro=='a':
        d = '2020-01-14'
        rep_id = list(rep['Report_No'])
        res_id = list(res['Report_No'])

        c = rep_id+res_id
        id=[x for x in c if c.count(x)==1]

        low = []
        mid = []
        high = []

        for i in id:
            ind = rep_id.index(i)
            if rep['Report_Date'][ind]==d and rep['Status'][ind]=='Low':
                low.append([rep['Lattitude'][ind],rep['Longitude'][ind]])
            elif rep['Report_Date'][ind]==d and rep['Status'][ind]=='Medium':
                mid.append([rep['Lattitude'][ind],rep['Longitude'][ind]])
            elif rep['Report_Date'][ind]==d and rep['Status'][ind]=='High':
                high.append([rep['Lattitude'][ind],rep['Longitude'][ind]])

        return low,mid,high

    elif pro=='b':
        d = '2020-01-14'
        rep_id = list(rep['Report_No'])
        res_id = list(res['Report_No'])

        c = rep_id+res_id
        id=[x for x in c if c.count(x)==1]

        l = []

        for i in id:
            ind = rep_id.index(i)
            if rep['Report_Date'][ind]!=d:
                l.append([rep['Lattitude'][ind],rep['Longitude'][ind]])
        return l

    elif pro=='c':
        d = '2020-01-14'
        rep_id = list(rep['Report_No'])
        res_id = list(res['Report_No'])

        l = []

        for i in res_id:
            ind = rep_id.index(i)
            if rep['Report_Date'][ind]==d:
                l.append([rep['Lattitude'][ind],rep['Longitude'][ind]])
        return l


def data_query2(place):
    d = '2020-01-14'

    rep = pd.read_csv('reports.csv')
    res = pd.read_csv('resolve.csv')

    if place in ['Ranjhi','Gol Bazar','Sadar','Ghamapur']:
        tot1 = rep.loc[rep['Area']==place]
        tot = tot1.loc[tot1['Report_Date']==d]
        tot = tot.reset_index()

        status = {'Low':0,'Medium':0,'High':0}

        for i in range(tot.shape[0]):
          if tot['Status'][i]=='Low':
            status['Low']+=1
          elif tot['Status'][i]=='Medium':
            status['Medium'] += 1
          elif tot['Status'][i]=='High':
            status['High'] += 1


        a = status['Low']+status['High']+status['Medium']
        status['Low'] = (status['Low']/a)*100
        status['Medium'] = (status['Medium']/a)*100
        status['High'] = (status['High']/a)*100

        joined = pd.merge(left=tot,right=res, left_on='Report_No', right_on='Report_No')
        non_res = tot.shape[0]-joined.shape[0]
        resolved = tot.shape[0]-non_res

        res_d = {'Resolved':resolved,'Not Resolved':non_res}
        return res_d,status


    else:
        # total reports today
        tot = rep.loc[rep['Report_Date']==d]
        tot = tot.reset_index()
        status = {'Low':0,'Medium':0,'High':0}
        for i in range(tot.shape[0]):
            if tot['Status'][i]=='Low':
                status['Low']+=1
            elif tot['Status'][i]=='Medium':
                status['Medium'] += 1
            elif tot['Status'][i]=='High':
                status['High'] += 1


        a = status['Low']+status['High']+status['Medium']
        status['Low'] = (status['Low']/a)*100
        status['Medium'] = (status['Medium']/a)*100
        status['High'] = (status['High']/a)*100

        joined = pd.merge(left=tot,right=res, left_on='Report_No', right_on='Report_No')
        non_res = tot.shape[0]-joined.shape[0]
        resolved = tot.shape[0]-non_res

        res_d = {'Resolved':resolved,'Not Resolved':non_res}

        return res_d,status


def report(img,date,time,area,status,lat,lon):
    file = open('reports.csv','a')
    df = pd.read_csv('reports.csv')
    ind = str(list(df['Report_No'])[-1]+1)
    s = ind+','+str(img)+','+str(date)+','+str(time)+','+str(status)+','+str(area)+','+str(lat)+','+str(lon)+'\n'
    file.write(s)
    file.close()

def resolve(no,date,time,emp_id):
    file = open('resolve.csv','a')
    s = str(no)+','+str(date)+','+str(time)+','+str(emp_id)+'\n'
    file.write(s)
    file.close()

def pred(filename):
    learn = load_learner('')
    img = open_image('Images/'+filename)
    s = str(learn.predict(img)[0])
    return(s)

def create_random_point(x0,y0):
    """
            Utility method for simulation of the points
    """
    r = 1000/ 111300
    u = np.random.uniform(0,1)
    v = np.random.uniform(0,1)
    w = r * np.sqrt(u)
    t = 2 * np.pi * v
    x = w * np.cos(t)
    x1 = x / np.cos(y0)
    y = w * np.sin(t)
    return (x0+x1, y0 +y)


app = Flask(__name__)

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
    e,d,a = funcs.data_query('a')
    b = funcs.data_query('b')
    c = funcs.data_query('c')
    return render_template("view.html",a=a,b=b,c=c,d=d,e=e)

@app.route("/week")
def week():
    l,m,h= funcs.dweek()
    return render_template("week.html", l=l,m=m,h=h)

@app.route("/pichart",methods=['GET','POST'])
def pichart():
    cls, status  = funcs.data_query2('other')
    per_r=cls['Resolved']
    per_nr=cls['Not Resolved']
    per_l=status['Low']
    per_m=status['Medium']
    per_h=status['High']

    return render_template("pichart.html",per_r=per_r,per_nr=per_nr,per_l=per_l,per_m=per_m,per_h=per_h)


@app.route("/piee",methods=['GET','POST'])
def piee():
    if request.method == 'POST':

        loc = str((request.form.get('menu')))
        cls, status  = funcs.data_query2(loc)
        loc=loc.lower()

    if loc=="ranjhi":
        per_r=cls['Resolved']
        per_nr=cls['Not Resolved']
        per_l=status['Low']
        per_m=status['Medium']
        per_h=status['High']

        return render_template("pichart.html",per_r=per_r,per_nr=per_nr,per_l=per_l,per_m=per_m,per_h=per_h)

    if loc=="gol bazar":
        per_r=cls['Resolved']
        per_nr=cls['Not Resolved']
        per_l=status['Low']
        per_m=status['Medium']
        per_h=status['High']

        return render_template("pichart.html",per_r=per_r,per_nr=per_nr,per_l=per_l,per_m=per_m,per_h=per_h)

    if loc=="sadar":
        per_r=cls['Resolved']
        per_nr=cls['Not Resolved']
        per_l=status['Low']
        per_m=status['Medium']
        per_h=status['High']

        return render_template("pichart.html",per_r=per_r,per_nr=per_nr,per_l=per_l,per_m=per_m,per_h=per_h)

    if loc=="ghamapur":
        per_r=cls['Resolved']
        per_nr=cls['Not Resolved']
        per_l=status['Low']
        per_m=status['Medium']
        per_h=status['High']

        return render_template("pichart.html",per_r=per_r,per_nr=per_nr,per_l=per_l,per_m=per_m,per_h=per_h)


@app.route("/submit", methods=['POST'])
def submit():
    f = request.files['fileToUpload']
    filename = f.filename
    f.save(filename)
    os.rename(filename, "Images/"+filename)
    s = pred(filename)
    #classes = ['Huge_Waste', 'Little_Waste', 'Medium_Waste']
    if s=='Huge_Waste':
      s = 'High'
    elif s=='Little_Waste':
      s = 'Low'
    elif s=='Medium_Waste':
      s = 'Medium'
    place = str(request.form.get('menu'))
    cord = {'Ranjhi':[23.195727, 79.995952],'Gol Bazar':[23.169591, 79.927285],'Sadar':[23.153795, 79.946919],'Ghamapur':[23.176642, 79.952820]}
    lat,lon = create_random_point(cord[place][0],cord[place][1])
    #d = date.today()
    d = '2020-01-14'
    now = datetime.now()
    t = now.strftime("%H:%M:%S")
    funcs.report(filename,d,t,place,s,lat,lon)
    return render_template("detect.html",s=s)


@app.route("/confrim", methods=['POST'])
def confrim():
    x= request.form.get('report')
    y= request.form.get('id')
    d = date.today()
    now = datetime.now()
    t = now.strftime("%H:%M:%S")
    funcs.resolve(x ,str(d),t,y )
    return render_template("index.html")


if __name__ == '__main__':
    app.run()
