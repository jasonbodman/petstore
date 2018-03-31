from flask import Flask, render_template, url_for, request, redirect

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

    # Set token for Google and Facebook
    auth_code = request.data

    # Connect via Google Sign in
    if provider == 'google':
        # Exchange for a token
        try:
            # Upgrade auth_code to a credentials object
            oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(auth_code)
        except FlowExchangeError:
            response = make_response(json.dumps('Failed to upgrade the authorization code'))
            response.headers['Content-Type'] = 'application/json'
            return response

        #Check that access token is valid
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])

        # If there was an error in the access token info, abort.
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'

        # Verify that the access token is used for the intended user.
        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        #Verify that the access token is valid for this app.
        if result['issued_to'] != CLIENT_ID:
            response = make_response(json.dumps("Token's client ID does not match app's."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        stored_credentials = login_session.get('credentials')
        stored_gplus_id = login_session.get('gplus_id')
        if stored_credentials is not None and gplus_id == stored_gplus_id:
            response = make_response(json.dumps('Current user is already connected.'), 200)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Store the access token in the session for later use.
        login_session['access_token'] = credentials.access_token
        login_session['gplus_id'] = gplus_id

        # Determine if user exists, if not commit to 'User' table
        # Get user info
        h = httplib2.Http()
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt':'json'}
        answer = requests.get(userinfo_url, params=params)

        data = answer.json()

        login_session['username'] = data['name']
        login_session['picture'] = data['picture']
        login_session['email'] = data['email']
        login_session['provider'] = 'google'

        # Check User table for user info
        user = session.query(User).filter_by(data['email']).first()
        if not user:
            user = User(username = login_session['username'], picture = login_session['picture'], email = login_session['email'])
            session.add(user)
            session.commit()

        # Create welcome message for user once login is complete
        output = ''
        output += '<h1>Welcome, '
        output += login_session['username']
        output += '!</h1>'
        output += '<img src="'
        output += login_session['picture']
        output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

        # Make token
        token = user.generate_auth_token(600)

        # Send token back to client
        return jsonify({'token': token.decode('ascii')})

    # Connect via Facebook Sign In
    if provider == 'facebook':
        # Exchange auth_code for token
        app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
        app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
        url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
            app_id, app_secret, auth_code)
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

        # Get user info
        data = json.loads(result)
        login_session['username'] = data["name"]
        login_session['email'] = data["email"]
        login_session['provider'] = 'facebook'
        login_session['facebook_id'] = data['id']

        # The token must be stored in the login_session in order to properly logout
        login_session['access_token'] = token

        # Get user picture from Facebook
        url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
        h = httplib2.Http()
        result = h.request(url, 'GET')[1]
        data = json.loads(result)
        login_session['picture'] = data["data"]["url"]

        # see if user exists
        user = session.query(User).filter_by(login_session['email']).first()
        if not user:
            user = User(username = login_session['username'], picture = login_session['picture'], email = login_session['email'])
            session.add(user)
            session.commit()

        # Create welcome message for user once login is complete
        output = ''
        output += '<h1>Welcome, '
        output += login_session['username']
        output += '!</h1>'
        output += '<img src="'
        output += login_session['picture']
        output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

        flash("Now logged in as %s" % login_session['username'])
        return output

    # Response if <provider> is not Facebook or Google
    else:
        return 'Unrecoginized Provider'



# Show all animal types
@app.route('/')
@app.route('/types')
def showTypes():
    types = session.query(Type).order_by(asc(Type.name))
    return render_template('types.html', types = types)

# Create a new animal type
@app.route('/types/new/', methods=['GET', 'POST'])
def newType():
    if request.method == 'POST':
        newType = Type(name = request.form['name'], user_id="1") # Temporary hold for UserID column
        session.add(newType)
        session.commit()
        return redirect(url_for('showTypes'))
    else:
        return render_template('newType.html')

# Edit a current animal type
@app.route('/types/<int:type_id>/edit', methods=['GET', 'POST'])
def editType(type_id):
    type = session.query(Type).filter_by(id = type_id).one()
    if request.method == 'POST':
        if request.form['name']:
            type.name = request.form['name']
            session.add(type)
            session.commit()
            return redirect(url_for('showTypes'))
    else:
        return render_template('editType.html', type = type)

# Delete a current animal type
@app.route('/types/<int:type_id>/delete', methods=['GET', 'POST'])
def deleteType(type_id):
    type = session.query(Type).filter_by(id = type_id).one()
    if request.method == 'POST':
        type = session.query(Type).filter_by(id = type_id).one()
        session.delete(type)
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
    return render_template('allPets.html', type = type, pets = pets)

# Create a new pet
@app.route('/types/<int:type_id>/pets/new/', methods=['GET', 'POST'])
def newPet(type_id):
    type = session.query(Type).filter_by(id = type_id).one()
    if request.method == 'POST':
        # Temporary hold for UserID column
        newPet = Pet(name = request.form['name'], description = request.form['description'], adopted = "1", type = type_id, user = "1")
        session.add(newPet)
        session.commit()
        return redirect(url_for('allPets', type_id = type_id))
    else:
        return render_template('newPet.html', type = type)

# Edit a current pet
@app.route('/types/<int:type_id>/pets/<int:pet_id>/edit', methods=['GET', 'POST'])
def editPet(type_id, pet_id):
    type = session.query(Type).filter_by(id = type_id).one()
    editedPet = session.query(Pet).filter_by(id = pet_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedPet.name = request.form['name']
        if request.form['description']:
            editedPet.description = request.form['description']
        if request.form['adopted']:
            editedPet.adopted = request.form['adopted']
        session.add(editedPet)
        session.commit()
        return redirect(url_for('allPets', type_id = type_id))
    else:
        return render_template('editPet.html', type = type, pet=editedPet)

# Delete a pet
@app.route('/types/<int:type_id>/pets/<int:pet_id>/delete', methods=['GET', 'POST'])
def deletePet(type_id, pet_id):
    type = session.query(Type).filter_by(id = type_id).one()
    pet = session.query(Pet).filter_by(id = pet_id).one()
    if request.method == 'POST':
        session.delete(pet)
        session.commit()
        return redirect(url_for('allPets', type_id = type_id))
    else:
        return render_template('deletePet.html', type=type, pet=pet)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
