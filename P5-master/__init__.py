# from flask import Flask
# app = Flask(__name__)
# @app.route("/")
# def hello():
#     return "H1Hello, I love Digital Ocean!"
# if __name__ == "__main__":
#     app.run()

from flask import Flask, render_template, request, redirect, url_for
from flask import jsonify, flash
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Event, User
# login
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import psycopg2
# Upload
import os
import sys
from flask import Flask, request, redirect, url_for
from werkzeug import secure_filename

# upload folder will be saved locally
UPLOAD_FOLDER = 'static/images/'

# check if images folder exists, if not create a new one
if not os.path.exists(os.path.join(os.getcwd(), UPLOAD_FOLDER)):
    os.makedirs(os.path.join(os.getcwd(), UPLOAD_FOLDER))
    print os.getcwd()
    print "makedir", os.path.join(os.getcwd(), UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'JPG', 'jpeg', 'JPEG',
                          'gif', 'GIF'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Get client ID from JSON client secret
CLIENT_ID = json.loads(
    open('google_login.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "City Events"

engine = create_engine("postgresql+psycopg2://eventlist:eventlist@localhost/eventlist")
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# Facebook login connection
# Facebook login function is commented because it does not works on html side
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    api_version = '2.5'

    # prevent cross-site request forgeries (CSRF)
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_login.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_login.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v{API}/me".format(API=api_version)
    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v{API}/me?{Token}&fields=name,id,email'.format(API=api_version, Token=token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    # let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v{API}/me/picture?{Token}&redirect=0&height=200&width=200'.format(API=api_version,
                                                                                                        Token=token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' "style = "width: 300px; height: 300px;border-radius: 150px; \
                -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' \
          % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


# Google Login connection function
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data
    print "Debug 2: ", code
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('google_login.json',
                                             scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)

    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token

    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)

    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])

    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;\
              -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
# ----------------------
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# These authentification codes are taken from https://github.com/udacity/ud330/
# Google disconnect-Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # see https://discussions.udacity.com/t/lesson-2-step-6-gdisconnect-error/15394
    access_token = login_session.get('credentials')

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# ----------------------------------------------------------------------------

# JSON API
@app.route('/categories/<int:category_id>/events/api/JSON')
def showApiEventsJSON(category_id):
    """JSON API endpoints"""
    events = session.query(Event).filter_by(category_id=category_id).all()
    return jsonify(Events=[i.serialize for i in events])


# Home
@app.route('/')
@app.route('/all')
def home():
    """Shows all events of all categories ordered by the latest added events"""
    categories = session.query(Category)
    events = session.query(Event).order_by(desc(Event.id))

    if 'username' not in login_session:
        return render_template('publicmain.html', categories=categories,
                               events=events, category_id=0)
    else:
        return render_template('main.html', categories=categories,
                               events=events, category_id=0,
                               user_id=login_session['user_id'])


@app.route('/categories/<int:category_id>/events')
def showEvents(category_id):
    """ Shows all events of a selected categories """
    category = session.query(Category).filter_by(id=category_id).one()
    events = session.query(Event).filter_by(category_id=category_id)
    if 'username' not in login_session:
        return render_template('restaurants.html',
                               categories=session.query(Category),
                               category_id=category_id,
                               events=events, category=category)
    else:
        return render_template('showevent.html',
                               categories=session.query(Category),
                               category_id=category_id, events=events,
                               category=category,
                               user_id=login_session['user_id'])


@app.route('/categories/<int:category_id>/add', methods=['GET', 'POST'])
def addEvent(category_id):
    """ Adds an event only for logged user """
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        # a user can add a image URL or a local path to upload an image
        # we need to differentiate the input
        use_local_image = False
        if request.form['url_image']:
            print request.form['url_image']
        else:
            use_local_image = True

        upload_file = request.files['local_image']
        imgfilename = os.path.join(app.config['UPLOAD_FOLDER'],
                                   upload_file.filename)
        # check for an uploaded image or URL image
        if use_local_image:
            if not upload_file or not allowed_file(upload_file.filename):
                flash('not successfully created due to wrong image file')
                return render_template('addevent.html',
                                       categories=session.query(Category),
                                       category_id=category_id)
            else:
                upload_file.save(imgfilename)

        newEvent = Event(name=request.form['name'],
                         description=request.form['description'],
                         price=request.form['price'],
                         category_id=category_id,
                         image='/' + imgfilename if use_local_image == True
                         else request.form['url_image'],
                         user_id=login_session['user_id'])
        session.add(newEvent)
        flash('A new Event %s is Successfully Created' % newEvent.name)
        session.commit()
        return redirect(url_for('showEvents', category_id=category_id))
    else:
        return render_template('addevent.html',
                               categories=session.query(Category),
                               category_id=category_id)


@app.route('/categories/<int:category_id>/<int:event_id>/edit',
           methods=['GET', 'POST'])
def editEvent(category_id, event_id):
    """Edits and updates event database"""
    editedEvent = session.query(Event).filter_by(id=event_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    # assure only for logged user
    if editedEvent.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized \
            to edit this event. Please create an admin account in order to \
            edit.');}</script><body onload='myFunction()''>"

    if request.method == 'POST':
        use_local_image = False
        # check if an URL or a local image is given
        if request.form['url_image']:
            print "url_image"
            print request.form['url_image']
        else:
            use_local_image = True
            print "local image"

        upload_file = request.files['local_image']
        imgfilename = os.path.join(app.config['UPLOAD_FOLDER'],
                                   upload_file.filename)

        # if a local image uploaded, the new image path will be updated
        # and the new image has to be saved
        if use_local_image:
            if not upload_file or not allowed_file(upload_file.filename):
                print "no upload file or not allowed file"
                return render_template('editevent.html', event=editedEvent,
                                       categories=session.query(Category),
                                       category_id=category_id)
            else:
                upload_file.save(imgfilename)
                editedEvent.image = '/' + imgfilename
        else:
            editedEvent.image = request.form['url_image']

        # Update database
        if request.form['name']:
            editedEvent.name = request.form['name']
        if request.form['description']:
            editedEvent.description = request.form['description']
        if request.form['price']:
            editedEvent.price = request.form['price']
        session.add(editedEvent)
        session.commit()
        return redirect(url_for('showEvents',
                                category_id=editedEvent.category_id))
    else:
        return render_template('editevent.html',
                               categories=session.query(Category),
                               category_id=category_id, event=editedEvent)


@app.route('/categories/<int:category_id>/<int:event_id>/delete',
           methods=['GET', 'POST'])
def deleteEvent(category_id, event_id):
    """delete event only by logged user."""
    eventToDelete = session.query(Event).filter_by(id=event_id).one()
    if 'username' not in login_session:
        return redirect('/login')

    # prevent cross-site request forgeries (CSRF)
    if eventToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized \
            to delete this event. Please create an admin account in order to \
            delete.');}</script><body onload='myFunction()''>"

    if request.method == 'POST':
        session.delete(eventToDelete)
        flash('%s Successfully Deleted' % eventToDelete.name)
        session.commit()
        return redirect(url_for('showEvents', category_id=category_id))
    else:
        return render_template('deleteevent.html',
                               categories=session.query(Category),
                               category_id=category_id, event=eventToDelete)


def allowed_file(filename):
    """image upload functionality"""
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def upload_file():
    """upload image filename"""
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file', filename=filename))


@app.route('/disconnect')
def disconnect():
    """Disconnect based on provider. route for logout"""
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('home'))
    else:
        flash("You were not logged in")
        return redirect(url_for('home'))


if __name__ == '__main__':
    app.secret_key = 'ultra_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=80)
