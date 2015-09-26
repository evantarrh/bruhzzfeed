from flask import Flask, render_template
from imgurpython import ImgurClient
import random
import config

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
  for category in categories:
    images_in_category = imgur.gallery_tag(category, sort="viral", window="day").items
    random.shuffle(images_in_category)
    images += images_in_category[0:10]
  return images

if __name__ == "__main__":
    app.run(host="0.0.0.0")
