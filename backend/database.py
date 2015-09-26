from pymongo import MongoClient
import string, random

client = MongoClient()
db = client.bruhzzfeed

def addPage(title, images):
# urlstring: random hash

  urlstring = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(6))
  entry = {"urlstring" : urlstring,
           "title" : title,
           "images" : images
  }

  db.pages.insert(entry)

  return urlstring

def getPage(urlstring):
  return db.pages.find_one({"urlstring": urlstring})
