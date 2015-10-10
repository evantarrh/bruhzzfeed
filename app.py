import os
from flask import Flask, render_template, url_for, make_response, redirect, request
from flask_limiter import Limiter
from imgurpython import ImgurClient
from backend import database as db
from clarifai.client import ClarifaiApi
import random, json, ast, operator, time
from topia.termextract import tag as part_of_speech
import structures, words

imgur = ImgurClient(os.environ['IMGUR_CLIENT_ID'], os.environ['IMGUR_CLIENT_SECRET'])
clarifai_api = ClarifaiApi()  # assumes environment variables are set.

pos_tagger = part_of_speech.Tagger()
pos_tagger.initialize()

app = Flask(__name__)
# app.config["DEBUG"] = True
limiter = Limiter(app)

@app.route("/")
def hello():
  categories = ['animals','tech','cats','dogs','funny','babies',
    'anime','gaming','music','nature','food','sports','celebs','reaction']
  return render_template("index.html", categories=categories)

@app.route("/new", methods=["POST"])
@limiter.limit("4/hour")
def create_article():
  """Given a bunch of categories, get popular images in those categories,
  tag them, find the most common tags, and create an article based on
  those tags and those images."""

  # take "categories=tech,anime,sports," and turn it into a list
  categories = request.get_data().split("=")[1]
  categories = categories.split(",")[0:-1]

  urls = get_imgur_images(categories)
  number_of_images = len(urls)

  # get most common tags for images, and get part of speech for all of them
  images_with_tags = get_tags(urls)

  common_tags = find_common_tags(images_with_tags)
  tags_with_pos = get_pos_for_tags(common_tags)

  # generate title based on tags with part of speech, and number of images
  title = get_title(tags_with_pos, len(urls))

  for tag_pair in images_with_tags:
    for tag in tag_pair[1]:
      speech_part = pos_tagger(tag)[0][1]
      # if it's an adjective, remove it from the tags sent to the database
      if speech_part == "JJ":
        tag_pair[1].remove(tag)

  random.shuffle(images_with_tags)
  urlstring = db.add_page(title, images_with_tags)

  return urlstring

@app.route("/<urlstring>", methods=["GET"])
def show_article(urlstring):
  info = db.get_page(urlstring)
  if info is None:
    return render_template('404.html')

  return render_template("article.html", title=info["title"], images=info["images"])

@app.route("/random", methods=["GET"])
def take_a_chance():
  return redirect("/" + db.get_random_page())

def get_imgur_images(categories):
  images = []

  total_number_of_images = int(random.choice(words.numbers))

  images_per_category = total_number_of_images / len(categories)

  # doing integer division to get the number of images per catgeory leaves leftovers!
  extra_images = total_number_of_images % len(categories)

  for category in categories:
    images_in_category = imgur.gallery_tag(category, sort="viral", window="week").items
    random.shuffle(images_in_category)

    image_count = 0
    for image in images_in_category:
      if image_count < images_per_category or extra_images > 0:
        # only keep image links that end in proper file extension
        if image.link.split('.')[-1] in ["gif", "png", "jpg"]:
          if extra_images > 0:
            extra_images -= 1
          else:
            image_count += 1
          images.append(image.link)

  return images

def get_tags(urls):
  all_tags = []
  for url in urls:

    clarifai_tags = clarifai_api.tag_image_urls(str(url))
    one_image_tags = json.dumps(clarifai_tags['results'][0]['result']['tag']['classes'])

    # json.dumps returns a string, which we have to evaluate as a list
    one_image_tags = ast.literal_eval(one_image_tags)

    # sometimes clarifai returns a list inside a list (for gifs).
    # if so, we just take the first list
    if type(one_image_tags[0]) is list:
      one_image_tags = one_image_tags[0]

    tuple = (str(url), one_image_tags)
    all_tags.append(tuple)

  return all_tags

def find_common_tags(tag_sets):
  tags_to_urls = {}
  for tag_tuple in tag_sets:
    tag_set = tag_tuple[1]
    for tag in tag_set:
      if tag in tags_to_urls:
        tags_to_urls[tag].append(tag_tuple[0])
      else:
        tags_to_urls[tag] = [tag_tuple[0]]

  tag_frequencies = {}

  for tag in tags_to_urls:
    tag_frequencies[tag] = len(tags_to_urls[tag])

  top_tags = {}
  for key in sorted(tag_frequencies, key=tag_frequencies.get, reverse=True)[0:10]:
    top_tags[key] = tags_to_urls[key]

  return top_tags

def get_pos_for_tags(tags_dict):
  tags_with_pos = {}
  for tag in tags_dict:
    tags_with_pos[tag] = pos_tagger(tag)[0][1]
  return tags_with_pos

def get_title(tags_with_pos, number_of_images):
  sentence = random.choice(structures.sentence_structures)

  nouns = []
  adjectives = []

  for tag in tags_with_pos:
    if tags_with_pos[tag] == "JJ":
      adjectives.append(tag)
    if tags_with_pos[tag] == "NN" or tags_with_pos[tag] == "NNS":
      nouns.append(tag)

  if "adverb" in sentence:
    adverb = random.choice(words.adverbs)
    sentence = sentence.replace("adverb", adverb.capitalize(), 1)

  while "nouns" in sentence and len(nouns) > 0:
    noun = random.choice(nouns)
    nouns.remove(noun)
    noun = pluralize(noun)
    sentence = sentence.replace("nouns", noun.capitalize(), 1)

  while "adjective" in sentence and len(adjectives) > 0:
    adjective = random.choice(adjectives)
    adjectives.remove(adjective)
    sentence = sentence.replace("adjective", adjective.capitalize(), 1)

  while "adjective" in sentence:
    adjective = random.choice(words.adjectives)
    sentence = sentence.replace("adjective", adjective.capitalize(), 1)

  while "verb" in sentence:
    verb = random.choice(words.verbs)
    sentence = sentence.replace("verb", verb.capitalize(), 1)

  if "exclamations" in sentence:
    exclamation = random.choice(words.exclamations)
    sentence = sentence.replace("exclamations", exclamation.capitalize())

  while "number" in sentence:
    sentence = sentence.replace("number", str(number_of_images), 1)

  while "years" in sentence:
    number = random.choice(words.years)
    sentence = sentence.replace("years", number, 1)

  return sentence

def pluralize(noun):
  """An incomplete but reasonable attempt at pluralizing tags given by Clarifai"""
  if noun == 'child':
    return 'children'

  last_letter = noun[len(noun) - 1]
  if last_letter == 'y':
    noun = noun[:-1] + 'ies'
  elif last_letter != 's':
    noun += 's'

  return noun

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
