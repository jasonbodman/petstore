from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Type, Pet

engine = create_engine('sqlite:///itemcatalog.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create dummy user
User1 = User(username="Jason Bodman", email="bodmand1@gmail.com", picture="https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png")
session.add(User1)
session.commit()

Type1 = Type(name="Cat", user_id="User1")
session.add(Type1)
session.commit()

Type2 = Type(name="Dog", user_id="User1")
session.add(Type2)
session.commit()

Pet1 = Pet(name="Ginny", type="Type1", description="Ginny is fun but lazy cat who isn't shy to let you know when it is meal time.", user="User1", adopted="1")
session.add(Pet1)
session.commit()


Pet2 = Pet(name="Penny", type="Type1", description="Penny is an adventerous cat who likes naps and tends to be shy.", user="User1", adopted="1")
session.add(Pet2)
session.commit()

Pet3 = Pet(name="Murphy", type="Type2", description="If you're looking for a furry friend who is ready for adventure and looking to make you happy, you've found him in Murphy!", user="User1", adopted="1")
session.add(Pet3)
session.commit()

print "added users and pets items!"
