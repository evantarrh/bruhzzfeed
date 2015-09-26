from flask import Flask, render_template, url_for, make_response, redirect
from imgurpython import ImgurClient
from backend import database as db
import random, config

client_id = config.imgur_client_id
client_secret = config.imgur_client_secret

imgur = ImgurClient(client_id, client_secret)

app = Flask(__name__)
app.config["DEBUG"] = True

@app.route("/")
def hello():
  categories = ["The More You Know", "funny", "cars"]
  pics = get_imgur_images(categories)
  return render_template("index.html", images=pics)

def get_imgur_images(categories):
  images = []
  images_per_category = 50 / len(categories)
  for category in categories:
    images_in_category = imgur.gallery_tag(category, sort="viral", window="day").items
    random.shuffle(images_in_category)
    images += images_in_category[0:images_per_category]
  return images

@app.route("/new", methods=["POST"])
def create_article():
  # get imgur images (return list of urls)
  # get tags for all the images
  # figure out common tags
  # select images most relevant to tags
  # use the tags to build an article name
  # make database entry with article name and URLs

  urlstring = db.addPage("fake title",
       ["http://i.imgur.com/RuxJy0U.jpg",
        "http://i.imgur.com/g16Zhpo.jpg",
        "http://i.imgur.com/UQprvMih.gif",
        "http://i.imgur.com/TyCh8dT.jpg",
        "http://i.imgur.com/JvLgTN0.jpg",
        "http://i.imgur.com/coqU8Mx.png"]
  )

  return redirect(url_for('show_article', urlstring=urlstring))

@app.route("/<urlstring>", methods=["GET"])
def show_article(urlstring):
  info = db.getPage(urlstring)
  if info is None:
    return render_template('404.html')

  return render_template("article.html", title=info["title"], images=info["images"])

if __name__ == "__main__":
    app.run(host="0.0.0.0")
