

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Event, User

engine = create_engine("postgresql+psycopg2://eventlist:eventlist@localhost/eventlist")
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create users
User1 = User(name="Cheesy", email="cheesydog@gmail.com",
             picture='')
session.add(User1)
session.commit()
User2 = User(name="", email="toonermediablah@gmail.com",
             picture='')
session.add(User2)
session.commit()

#--------Culture---------
category_culture = Category(name="Fastfood")

session.add(category_culture)
session.commit()

event1 = Event(name="placeholder", description="placeholder",
			   image="https://placeholdit.imgix.net/~text?txtsize=33&txt=350%C3%97150&w=350&h=150",
               price="$$$", category=category_culture, user_id=User1.id)

session.add(event1)
session.commit()


event2 = Event(name="placeholder",
			   description="placeholder",
               price="$$$", category=category_culture, user_id=User2.id,
               image="https://placeholdit.imgix.net/~text?txtsize=33&txt=350%C3%97150&w=350&h=150")

session.add(event2)
session.commit()


#--------Night Life---------
category_nightlife = Category(name="Italian")

session.add(category_nightlife)
session.commit()


event1 = Event(name="placeholder", description="placeholder",
			   image="https://placeholdit.imgix.net/~text?txtsize=33&txt=350%C3%97150&w=350&h=150",
               price="$$$", category=category_culture, user_id=User1.id)

session.add(event1)
session.commit()


event2 = Event(name="placeholder",
			   description="placeholder",
               price="$$$", category=category_culture, user_id=User2.id,
               image="https://placeholdit.imgix.net/~text?txtsize=33&txt=350%C3%97150&w=350&h=150")

session.add(event2)
session.commit()

#--------Sport---------
category_sport = Category(name="Sport")

session.add(category_sport)
session.commit()

event1 = Event(name="placeholder", description="placeholder",
			   image="https://placeholdit.imgix.net/~text?txtsize=33&txt=350%C3%97150&w=350&h=150",
               price="$$$", category=category_culture, user_id=User1.id)

session.add(event1)
session.commit()


event2 = Event(name="placeholder",
			   description="placeholder",
               price="$$$", category=category_culture, user_id=User2.id,
               image="https://placeholdit.imgix.net/~text?txtsize=33&txt=350%C3%97150&w=350&h=150")

session.add(event2)
session.commit()

#-------Culinary----------
category_culinary = Category(name="Culinary")

session.add(category_culinary)
session.commit()
event1 = Event(name="placeholder", description="placeholder",
			   image="https://placeholdit.imgix.net/~text?txtsize=33&txt=350%C3%97150&w=350&h=150",
               price="$$$", category=category_culture, user_id=User1.id)

session.add(event1)
session.commit()


event2 = Event(name="placeholder",
			   description="placeholder",
               price="$$$", category=category_culture, user_id=User2.id,
               image="https://placeholdit.imgix.net/~text?txtsize=33&txt=350%C3%97150&w=350&h=150")

session.add(event2)
session.commit()
print "added restaurant!"
