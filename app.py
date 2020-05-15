from flask import Flask, url_for, render_template

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

app.run(debug=True)