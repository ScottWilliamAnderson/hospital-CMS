
from medications import medicationsList, generateChart
from flask import Flask, g, url_for, redirect, render_template, request, session, abort, flash, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from functools import wraps
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, func

from flask_track_usage import TrackUsage
from flask_track_usage.storage.sql import SQLStorage
from flask_track_usage.storage.mongo import MongoEngineStorage
from flask_track_usage.summarization import sumRemote, sumUrl, sumUserAgent


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db' #configuring database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #causes significant overhead if True

# Tracks cookies - used for unique visitor count
app.config['TRACK_USAGE_COOKIE'] = True

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

engine = create_engine('sqlite:///data.db', echo = True)
meta = MetaData()


#Creates a table for login form with id, email and password
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)

#Creates a table for web page content with id and text
class Content(db.Model):
    page_id = db.Column(db.Integer, primary_key=True)
    header = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)

db.create_all()

#
# TrackUsage Setup
#
pstore = SQLStorage(db=db)
t = TrackUsage(app, [pstore])


#Populate content table with input from add new page content
@app.route("/populateContent", methods=['POST'])
def populateContent():
    inputString = request.form['editBox']
    #INSERT INTO content (content) VALUES (inputString)
    newContent = Content(content = inputString)
    db.session.add(newContent)
    db.session.commit()
    return redirect(url_for('index'))

#Update content table with input from edit.html
@app.route("/updateContent", methods=['POST'])
def updateContent():
    inputString = request.form['editBox']
    conn = engine.connect()
    #UPDATE first row in table content
    updateStatement = f'UPDATE Content SET content="{inputString}" WHERE page_id=1'
    result = conn.execute(updateStatement)
    return redirect(url_for('index'))

@app.route('/index')
#content table query for index.html
def retrieveContentIndex():
    conn = engine.connect()
    select = "SELECT * FROM Content"
    result = conn.execute(select)
    outputRow = result.fetchone()
    for row in result:
        if (row.page_id == 1):
            outputRow = row
    return render_template('index.html', content=outputRow.content)

@app.route('/edit')
#content table query for Edit.html
def retrieveContentEdit():
    conn = engine.connect()
    select = "SELECT * FROM Content"
    result = conn.execute(select)
    outputRow = result.fetchone()
    for row in result:
        if (row.page_id == 1):
            outputRow = row
    return render_template('edit.html', content=outputRow.content)




@app.route('/medication', methods=['GET', 'POST'])
def medication():
    if request.method == 'POST':
        selected = [med for med in medicationsList if med.name in request.form]
        return render_template('chart.html', chart=generateChart(selected))

    return render_template('medication.html', medications=medicationsList)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@app.route('/home')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/about')
def about():
    return render_template('about.html')



@app.route('/login')
def login():
    return render_template('auth/login.html')

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login'))

    return wrap

@app.route("/logmein", methods=['POST'])
def logmein():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(email = username).first()

    if not user:
        flash('Invalid credentials')
        return redirect(url_for('login'))
    else:
        if user.password != password:
            flash('Invalid credentials')
            return redirect(url_for('login'))
        else:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))



@app.route("/logout")
@login_required
def logout():
    session['logged_in'] = False
    session.clear()
    return redirect(url_for('index'))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route("/edit")
@login_required
def edit():
    return render_template('edit.html')


@app.route("/users")
@login_required
def users():
    conn = engine.connect()
    query = "SELECT id, email from user"
    result = conn.execute(query)
    data = result.fetchall()
    return render_template('users.html', data = data)


@app.route("/addUser")
@login_required
def addUser():
    return render_template('addUser.html')

@app.route("/addContentUser", methods=['POST'])
def addContentUser():
    userEmail = request.form['userEmail']
    userPassword = request.form['userPassword']
    user = User(email = userEmail, password = userPassword)
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('users'))


############# FOR TESTING SEARCHBAR #########
@app.route("/searchBarSample")
def searchBarSample():
    return render_template('searchBarSample.html')
#############################################

@app.route("/dashboard")
def userPlatformUsage():
    return render_template('dashboard.html', platformUsage=session.query(flask_usage).filter_by(ua_platform='windows').count())




if __name__ == '__main__':
    app.secret_key = '_5#y2L"F4Q8z\n\xec]/'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.debug = True
    app.run()
