from flask import Flask, render_template, url_for, make_response, redirect, request
from imgurpython import ImgurClient
from backend import database as db
from clarifai.client import ClarifaiApi
import random, config

client_id = config.imgur_client_id
client_secret = config.imgur_client_secret

imgur = ImgurClient(client_id, client_secret)
clarifai_api = ClarifaiApi()  # assumes environment variables are set.

app = Flask(__name__)
app.config["DEBUG"] = True

@app.route("/")
def hello():
    # tags = clarifai_api.tag_image_urls('http://www.clarifai.com/img/metro-north.jpg')
    return render_template("index.html")

def get_imgur_images(categories):
  images = []
  images_per_category = 100 / len(categories)
  for category in categories:
    images_in_category = imgur.gallery_tag(category, sort="viral", window="day").items
    random.shuffle(images_in_category)

    # remove images that don't end in proper file type
    for image in images_in_category[0:images_per_category]:
      if image.link.split('.')[-1] in ["gif", "png", "jpg"]:
        images.append(image.link)
  return images

@app.route("/new", methods=["POST"])
def create_article():
  # get imgur images (return list of urls)
  # get tags for all the images
  # figure out common tags
  # select images most relevant to tags
  # use the tags to build an article name
  # make database entry with article name and URLs

  print request.get_data()

  urlstring = db.addPage("fake title",
       ["http://i.imgur.com/RuxJy0U.jpg",
        "http://i.imgur.com/g16Zhpo.jpg",
        "http://i.imgur.com/UQprvMih.gif",
        "http://i.imgur.com/TyCh8dT.jpg",
        "http://i.imgur.com/JvLgTN0.jpg",
        "http://i.imgur.com/coqU8Mx.png"]
  )

  return urlstring

@app.route("/<urlstring>", methods=["GET"])
def show_article(urlstring):
  info = db.getPage(urlstring)
  if info is None:
    return render_template('404.html')

  return render_template("article.html", title=info["title"], images=info["images"])

if __name__ == "__main__":
    app.run(host="0.0.0.0")
