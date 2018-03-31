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
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

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
