import sqlalchemy
# for connecting with firestorage
import pyrebase
import os
# import employee_id
import pandas as pd

rdb = sqlalchemy.create_engine("mysql+pymysql://root:password@localhost/waste_management",
                                  pool_size=5,
                                  max_overflow=2,
                                  pool_timeout=30,
                                  pool_recycle=1800)


# function to add row in the reports table
def add_row(row):
    filename = row['filename']
    report_time = row['report_time']
    state = row['state']
    district = row['district']
    lattitude = row['lattitude']
    longitude = row['longitude']
    label = row['label']
    resolved = row['resolved']
    emp_ID = row['emp_ID']
    pick_time = row['pick_time']

    stmt = sqlalchemy.text(
        "INSERT INTO reports"
        "(state, district, lattitude, longitude, report_time, label, pick_time, resolved, emp_ID, filename)"
        "VALUES (:state, :district, :lattitude,	:longitude, :report_time, :label, :pick_time, :resolved, :emp_ID, :filename);"
    )

    try:
        with rdb.connect() as conn:
            conn.execute(stmt, state=state, district=district,
                         lattitude=lattitude, longitude=longitude,
                         report_time=report_time, label=label, pick_time=pick_time,
                         resolved=resolved, emp_ID=emp_ID, filename=filename)
    except:
        return("Error")

    return("Database Updated")


def check():
    with rdb.connect() as conn:
        res = conn.execute("select label, count(label) as count from reports group by label;").fetchall()
    return(res)


def add_csv_data():
    df = pd.read_csv('real_reports.csv')
    
    try:
        with rdb.connect() as conn:
            last = conn.execute("select report_no from reports order by report_no desc limit 1;").fetchone()[0]
    except:
        last = 0   
    
    df = df.loc[last:,:]
    

    stmt = sqlalchemy.text(
            "INSERT INTO reports"
            "(state, district, lattitude, longitude, report_time, label, pick_time, resolved, emp_ID, filename)"
            "VALUES (:state, :district, :lattitude,	:longitude, :report_time, :label, :pick_time, :resolved, :emp_ID, :filename);"
        )
    for i in range(df.shape[0]):
        with rdb.connect() as conn:
            conn.execute(stmt, state=df['state'][i], district=df['district'][i],
                         lattitude=str(df['lattitude'][i]), longitude=str(df['longitude'][i]),
                         report_time=df['report_time'][i], label=df['label'][i], pick_time=df['pick_time'][i],
                         resolved=str(df['resolved'][i]), emp_ID=df['emp_id'][i], filename=df['filename'][i])
    return('Yess')


class MainQuery:
    def __init__(self, state='all', district='all', start_date='2019-08-15', end_date='2020-08-15'):
        self.state = state
        self.district = district
        self.start_date = start_date
        self.end_date = end_date

    def get_coords(self):
        # to get the coordinates and label
        if self.state == 'all':
            stmt = sqlalchemy.text(
                "select label, lattitude, longitude from reports "
                "where report_time between :start_date and :end_date;"
    )
        else:
            if self.district == 'all':
                stmt = sqlalchemy.text(
                        "select label, lattitude, longitude from reports "
                        "where state=:state and (report_time between :start_date and :end_date);"
                        )
            else:
                stmt = sqlalchemy.text(
                        "select lattitude,longitude,label from reports "
                        "where (state=:state and district=:district) and (report_time between :start_date and :end_date);"
                        )
        with rdb.connect() as conn:
            res = conn.execute(stmt, state=self.state, district=self.district,
                                start_date=self.start_date, end_date=self.end_date).fetchall()
        # here convert the res to desired data form and return

    def get_label_count(self):
        # get the labels and counts of labels
        if self.state == 'all':
            stmt = sqlalchemy.text(
                            "select label, count(label) as count from reports "
                            "where report_time between :start_date and :end_date "
                            "group by label;"
                            )
        else:
            if self.district == 'all':
                stmt = sqlalchemy.text(
                            "select label, count(label) as count from reports "
                            "where state=:state and (report_time between :start_date and :end_date) "
                            "group by label;"
                    )
            else:
                stmt = sqlalchemy.text(
                        "select label, count(label) as count from reports "
                        "where (state=:state and district=:district) and (report_time between :start_date and :end_date) "
                        "group by label;"
                        )
        with rdb.connect() as conn:
            res = conn.execute(stmt, state=self.state, district=self.district,
                               start_date=self.start_date, end_date=self.end_date).fetchall()
        d = {}
        for row in res:
            d[row[0]] = row[1]
        return(d)


    def get_resolved_count(self):
        # get the count of resolved ontime and resolved late
        if self.state == 'all':
            stmt = sqlalchemy.text(
                        "select resolved, count(resolved) as count from reports "
                        "where report_time between :start_date and :end_date "
                        "group by resolved;"
                        )
        else:
            if self.district == 'all':
                stmt = sqlalchemy.text(
                            "select resolved, count(resolved) as count from reports "
                            "where state=:state and (report_time between :start_date and :end_date) "
                            "group by resolved;"
                            )
            else:
                stmt = sqlalchemy.text(
                            "select resolved, count(resolved) as count from reports "
                            "where (state=:state and district=:district) and (report_time between :start_date and :end_date) "
                            "group by resolved;")
        with rdb.connect() as conn:
            res = conn.execute(stmt, state=self.state, district=self.district,
                                start_date=self.start_date, end_date=self.end_date).fetchall()
        d = {}
        for row in res:
            d[row[0]] = row[1]
        return(d)
    
    
    def get_barplot_data(self):
        # to get the daily and weekly data about barplot
        if self.state == 'all':
            stmt = sqlalchemy.text(
                        "select distinct date(report_time) as report_date, label ,count(label) as count from reports "
                        "where report_time between :start_date and :end_date "
                        "group by report_date, label order by report_date;"
                        )
        else:
            if self.district == 'all':
                stmt = sqlalchemy.text(
                            "select distinct date(report_time) as report_date, label ,count(label) as count from reports "
                            "where state=:state and (report_time between :start_date and :end_date) "
                            "group by report_date, label order by report_date;"
                            )
            else:
                stmt = sqlalchemy.text(
                            "select distinct date(report_time) as report_date, label ,count(label) as count from reports "
                            "where (state=:state and district=:district) and (report_time between :start_date and :end_date) "
                            "group by report_date, label order by report_date;"
                            )
        with rdb.connect() as conn:
            res = conn.execute(stmt, state=self.state, district=self.district,
                                start_date=self.start_date, end_date=self.end_date).fetchall()
        
        d = {}
        for row in res:
            date = row[0].strftime("%d-%m-%Y")
            label = row[1]
            count = row[2]
            try:
                d[date][label] = count
            except:
                d[date] = {}
                d[date][label] = count
                
        daily = []
        dates = list(d.keys())
        for date in dates:
            d2 = {'Low':0, 'Medium':0, 'High':0, 'Total':0}
            label_count = d[date]
            for label in label_count.keys():
                if label == 'L':
                    d2['Low'] = label_count[label]
                elif label == 'M':
                    d2['Medium'] = label_count[label]
                elif label == 'H':
                    d2['High'] = label_count[label]
            d2['Total'] = d2['Low']+d2['Medium']+d2['High']
            daily.append(d2)
            
        weekly = []
        for i in range(0,len(daily), 7):
            week = {'Low':0, 'Medium':0, 'High':0, 'Total':0}
            for day in daily[i:i+7]:
                week['Low'] += day['Low']
                week['Medium'] += day['Medium']
                week['High'] += day['High']
                week['Total'] += day['Total']
            weekly.append(week)
        
        return(daily, weekly)
