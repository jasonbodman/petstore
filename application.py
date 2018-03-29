from flask import Flask, render_template, url_for, request, redirect

# Database Connection
from database_setup import Base, Type, Pet, User
from sqlalchemy import create_engine, asc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

app = Flask(__name__)

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Show all animal types
@app.route('/')
@app.route('/types')
def showTypes():
    types = session.query(Type).order_by(asc(Type.name))
    return render_template('types.html', types = types)

# Create a new animal type
@app.route('/types/new/')
def newType():
    if request.method == 'POST':
        newType = Type(name = request.form['name'])
        session.add(newType)
        session.commit()
        return redirect(url_for('showTypes'))
    else:
        return render_template('newType.html')

# Edit a current animal type
@app.route('/types/<int:type_id>/edit')
def editType(type_id):
    type = session.query(Type).filter_by(id = type_id).one()
    if request.method == 'POST':
        if request.form['name']:
            type.name = request.form['name']
            session.add(type)
            session.commit()
            return redirect(url_for('showTypes'))
    else:
        return render_template('editType.html')

# Delete a current animal type
@app.route('/types/<int:type_id>/delete')
def deleteType(type_id):
    if request.method == 'POST':
        type = session.query(Type).filter_by(id = type_id).one()
        session.delete(type)
        session.commit()
        return redirect(url_for('showTypes'))
    else:
        return render_template('deleteType.html')

# Show pets for a specific animal type
@app.route('/types/<int:type_id>/')
@app.route('/types/<int:type_id>/pets/')
def allPets(type_id):
    type = session.query(Type).filter_by(id = type_id).one()
    pets = session.query(Pet).filter_by(type = type_id).order_by(asc(Pet.name)).all()
    return render_template('allPets.html', type = type, pets = pets)

# Create a new pet
@app.route('/types/<int:type_id>/pets/new/')
def newPet(type_id):
    if request.method == 'POST':
        # UserID temporarily pulling from radio button on 'newPet'
        newPet = Pet(name = request.form['name'], description = request.form['decription'], adpoted = request.form['adopted'], type = type_id, user_id = request.form['user'])
        session.add(newPet)
        session.commit()
        return redirect(url_for('allPets', type_id = type_id))
    else:
        return render_template('newPet.html', type_id = type_id)

# View details about a specific pet
@app.route('/types/<int:type_id>/pets/<int:pet_id>/')
def showPet(type_id, pet_id):
    type = session.query(Type).filter_by(id = type_id).one()
    pet = session.query(Pet).filter_by(id = pet_id).one()
    return render_template('showPet.html', type = type, pet = pet)

# Edit a current pet
@app.route('/types/<int:type_id>/pets/<int:pet_id>/edit')
def editPet(type_id, pet_id):
    type = session.query(Type).filter_by(id = type_id).one()
    pet = session.query(Pet).filter_by(id = pet_id).one()
    if request.method == 'POST':
        if request.form['name']:
            pet.name = request.form['name']
        if request.form['description']:
            pet.description = request.form['description']
        if request.form['adopted']:
            pet.adopted = request.form['adopted']
        session.add(pet)
        session.commit()
        return redirect(url_for('allPets', type_id = type_id))
    else:
        return render_template('editPet.html', type_id = type_id, pet_id = pet_id)

# Delete a pet
@app.route('/types/<int:type_id>/pets/<int:pet_id>/delete')
def deletePet(type_id, pet_id):
    type = session.query(Type).filter_by(id = type_id).one()
    pet = session.query(Pet).filter_by(id = pet_id).one()
    if request.method == 'POST':
        session.delete(pet)
        session.commit()
        return redirect(url_for('allPets', type_id = type_id))
    else:
        return render_template('deletePet.html', type_id = type_id, pet_id = pet_id)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
