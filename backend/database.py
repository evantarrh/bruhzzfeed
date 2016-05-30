from pymongo import MongoClient
import string, random, os

mongolab_uri = os.environ.get('MONGOLAB_URI')

# if production
if mongolab_uri:
  client = MongoClient(mongolab_uri,
                     connectTimeoutMS=30000,
                     socketTimeoutMS=None,
                     socketKeepAlive=True)
  db = client.get_default_database()
else:
  client = MongoClient()
  db = client.bruhzzfeed

def add_page(title, images):
# urlstring: random hash

  urlstring = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(6))
  entry = {"urlstring" : urlstring,
           "title" : title,
           "images" : images
  }

  db.bruhzzfeed_pages.insert(entry)

  return urlstring

def get_page(urlstring):
  return db.bruhzzfeed_pages.find_one({"urlstring": urlstring})

def get_all_articles():
  return db.bruhzzfeed_pages.find()

def get_random_page():
  all_pages = db.bruhzzfeed_pages.find()
  urls = []
  for page in all_pages:
    urls.append(page["urlstring"])

  # if there's nothing in the DB, just add a slash so that it will reload homepage
  if not len(urls):
    urls.append("/")

  return random.choice(urls)
