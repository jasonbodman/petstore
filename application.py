from flask import Flask, render_template, url_for, request, redirect, flash

# Database Connection
from database_setup import Base, Type, Pet, User
from sqlalchemy import create_engine, asc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

# Authentication requirements
from flask import session as login_session
from flask_httpauth import HTTPBasicAuth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from flask import make_response
import requests, random, string, json

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = 'Item Catalog Application'

app = Flask(__name__)

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# User Authentication
#Create Anti-Forgery State Token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/oauth/<provider>', methods = ['POST'])
def login(provider):
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

# Connect via Google Plus Sign In

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
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
        return response

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

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
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
    output += ' " style = "width: 150px; height: 150px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    print "done!"
    flash("Welcome! You are now logged in as %s" % login_session['username'])
    return output

# Connect via Facebook Sign In
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
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
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
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
    output += ' " style = "width: 150px; height: 150px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("Welcome! You are now logged in as %s" % login_session['username'])
    return output

@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showTypes'))
    else:
        flash("You were not logged in.")
        return redirect(url_for('showTypes'))


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


# Disconnect - revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# Return user id if email is stored in user database
def getUserID(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

# Return user object associated with id number
def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

# Create new user
def createUser(login_session):
    newUser = User(name = login_session['username'], email = login_session['email'],
    picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id



# Show all animal types
@app.route('/')
@app.route('/types')
def showTypes():
    types = session.query(Type).order_by(asc(Type.name))
    if 'username' not in login_session:
        return render_template('publicTypes.html', types = types)
    else:
        return render_template('types.html', types = types)
    return render_template('publicTypes.html', types = types)

# Create a new animal type
@app.route('/types/new/', methods=['GET', 'POST'])
def newType():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newType = Type(name = request.form['name'], user_id="1") # Temporary hold for UserID column
        session.add(newType)
        flash("New animal type, %s, successfully created!" % newType.name)
        session.commit()
        return redirect(url_for('showTypes'))
    else:
        return render_template('newType.html')

# Edit a current animal type
@app.route('/types/<int:type_id>/edit', methods=['GET', 'POST'])
def editType(type_id):
    type = session.query(Type).filter_by(id = type_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name']:
            type.name = request.form['name']
            session.add(type)
            flash("%s successfully edited!" % type.name)
            session.commit()
            return redirect(url_for('showTypes'))
    else:
        return render_template('editType.html', type = type)

# Delete a current animal type
@app.route('/types/<int:type_id>/delete', methods=['GET', 'POST'])
def deleteType(type_id):
    type = session.query(Type).filter_by(id = type_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        type = session.query(Type).filter_by(id = type_id).one()
        session.delete(type)
        flash("%s successfully deleted!" % type.name)
        session.commit()
        return redirect(url_for('showTypes'))
    else:
        return render_template('deleteType.html', type = type)

# Show pets for a specific animal type
@app.route('/types/<int:type_id>/')
@app.route('/types/<int:type_id>/pets/')
def allPets(type_id):
    type = session.query(Type).filter_by(id = type_id).one()
    pets = session.query(Pet).filter_by(type = type_id).order_by(asc(Pet.name)).all()
    if 'username' not in login_session:
        return render_template('publicAllPets.html', type = type, pets = pets)
    else:
        return render_template('allPets.html', type = type, pets = pets)

# Create a new pet
@app.route('/types/<int:type_id>/pets/new/', methods=['GET', 'POST'])
def newPet(type_id):
    type = session.query(Type).filter_by(id = type_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        # Temporary hold for UserID column
        newPet = Pet(name = request.form['name'], description = request.form['description'], adopted = "1", type = type_id, user = "1")
        session.add(newPet)
        flash("Created new pet, %s" % newPet.name)
        session.commit()
        return redirect(url_for('allPets', type_id = type_id))
    else:
        return render_template('newPet.html', type = type)

# Edit a current pet
@app.route('/types/<int:type_id>/pets/<int:pet_id>/edit', methods=['GET', 'POST'])
def editPet(type_id, pet_id):
    type = session.query(Type).filter_by(id = type_id).one()
    editedPet = session.query(Pet).filter_by(id = pet_id).one()
    creator = getUserInfo(editedPet.user)
    if 'username' not in login_session:
        return redirect('/login')
    if 'username' != creator.id:
        flash("You do not have proper access to edit this pet's information.")
        return redirect(url_for('allPets', type_id = type_id))
    if request.method == 'POST':
        if request.form['name']:
            editedPet.name = request.form['name']
        if request.form['description']:
            editedPet.description = request.form['description']
        if request.form['adopted']:
            editedPet.adopted = request.form['adopted']
        session.add(editedPet)
        flash("Successfully edited %s's details" % editedPet.name)
        session.commit()
        return redirect(url_for('allPets', type_id = type_id))
    else:
        return render_template('editPet.html', type = type, pet=editedPet)

# Delete a pet
@app.route('/types/<int:type_id>/pets/<int:pet_id>/delete', methods=['GET', 'POST'])
def deletePet(type_id, pet_id):
    type = session.query(Type).filter_by(id = type_id).one()
    pet = session.query(Pet).filter_by(id = pet_id).one()
    creator = getUserInfo(pet.user)
    if 'username' not in login_session:
        return redirect('/login')
    if 'username' != creator.id:
        flash("You do not have proper access to edit this pet's information.")
        return redirect(url_for('allPets', type_id = type_id))
    if request.method == 'POST':
        session.delete(pet)
        flash("Successfully deleted %s" % pet.name)
        session.commit()
        return redirect(url_for('allPets', type_id = type_id))
    else:
        return render_template('deletePet.html', type=type, pet=pet)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
