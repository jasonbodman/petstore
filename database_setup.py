import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Type(Base):
    __tablename__ = "type"

    name = Column(String(32), nullable = False)
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('user.id'))

class Pet(Base):
    __tablename__ = 'pet'

    name = Column(String(32), nullable = False)
    id = Column(Integer, primary_key = True)
    type = Column(Integer, ForeignKey('type.id'))
    description = Column(String)
    user = Column(Integer, ForeignKey('user.id'))
    
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    username = Column(String(32), index = True)
    picture = Column(String)
    email = Column(String)

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.create_all(engine)
