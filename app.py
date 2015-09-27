import os
from flask import Flask, render_template, url_for, make_response, redirect, request
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
app.config["DEBUG"] = True

@app.route("/")
def hello():
    categories = ['animals','tech','cats','dogs','funny','babies',
      'anime','gaming','music','nature','food','sports','celebs','reaction']
    random_url = db.getRandomPage()
    return render_template("index.html", categories=categories, link=random_url)

def get_imgur_images(categories):
  images = []

  total_number_of_images = int(random.choice(words.numbers))

  images_per_category = total_number_of_images / len(categories)

  extra_images = total_number_of_images - len(categories) * images_per_category

  for category in categories:
    images_in_category = imgur.gallery_tag(category, sort="viral", window="week").items
    random.shuffle(images_in_category)

    image_count = 0
    for image in images_in_category:
      if image_count < images_per_category or extra_images > 0:
        if image.link.split('.')[-1] in ["gif", "png", "jpg"]:
          if extra_images > 0:
            extra_images -= 1
          else:
            image_count += 1
          images.append(image.link)

  tuple_to_return = (images, total_number_of_images)
  return tuple_to_return

@app.route("/new", methods=["POST"])
def create_article():
  print "handling post request"
  starting_time = time.time()

  # take "categories=tech,anime,sports," and turn it into a list
  categories = request.get_data().split("=")[1]
  categories = categories.split(",")[0:-1]

  images_and_number = get_imgur_images(categories)
  urls = images_and_number[0]

  print "got images! " + str(time.time() - starting_time)

  number_of_images = images_and_number[1]

  # get tags for all the images ============================================

  tags = get_tags(urls)
  print "tagged the images! " + str(time.time() - starting_time)

  # figure out common tags =================================================

  common_tags = find_common_tags(tags)

  tags_to_pos = get_pos_for_tags(common_tags)
  print "got parts of speech for tags! " + str(time.time() - starting_time)

  # choose tags based on pos

  noun_tags = []
  plural_noun_tags = []
  adjective_tags = []

  for tag in tags_to_pos:
    if tags_to_pos[tag] == "JJ":
      adjective_tags.append(tag)
    if tags_to_pos[tag] == "NN":
      noun_tags.append(tag)
    if tags_to_pos[tag] == "NNS":
      plural_noun_tags.append(tag)

  title = get_title(noun_tags, plural_noun_tags, adjective_tags, number_of_images)

  images = []

  for url in urls:
    tags_list = []

    for pair in tags:
      if pair[1] == url:
        for individual_tag in pair[0]:
          speech_part = pos_tagger(individual_tag)[0][1]
          if speech_part == "NN":
            tags_list.append(individual_tag)

    new_tuple = (str(url), tags_list)
    images.append(new_tuple)

  random.shuffle(images)

  urlstring = db.addPage(title, images)

  print "added page /" + urlstring + " to database! " + str(time.time() - starting_time)

  return urlstring

@app.route("/<urlstring>", methods=["GET"])
def show_article(urlstring):
  info = db.getPage(urlstring)
  if info is None:
    return render_template('404.html')

  return render_template("article.html", title=info["title"], images=info["images"])


def get_tags(urls):
  all_tags = []
  for i in urls:
    one_image_tags = json.dumps(clarifai_api.tag_image_urls(str(i))['results'][0]['result']['tag']['classes'])

    # json.dumps returns a string, which we have to evaluate as a list
    one_image_tags = ast.literal_eval(one_image_tags)

    # sometimes clarifai returns a list inside a list
    if type(one_image_tags[0]) is list:
      one_image_tags = one_image_tags[0]

    tuple = (one_image_tags, str(i))

    all_tags.append(tuple)

  return all_tags

def find_common_tags(tag_sets):
  tags_to_urls = {}
  for tag_tuple in tag_sets:
    tag_set = tag_tuple[0]
    for tag in tag_set:
      if tag in tags_to_urls:
        tags_to_urls[tag].append(tag_tuple[1])
      else:
        tags_to_urls[tag] = [tag_tuple[1]]


  tag_frequencies = {}

  for tag in tags_to_urls:
    tag_frequencies[tag] = len(tags_to_urls[tag])

  top_tags = {}
  for key in sorted(tag_frequencies, key=tag_frequencies.get, reverse=True)[0:10]:
    top_tags[key] = tags_to_urls[key]

  return top_tags

def get_pos_for_tags(tags_dict):
  tags_to_pos = {}
  for tag in tags_dict:
    tags_to_pos[tag] = pos_tagger(tag)[0][1]
  return tags_to_pos

def get_title(nouns, plural_nouns, adjectives, number_of_images):
  sentence = random.choice(structures.sentence_structures)

  tags = []

  if "adverb" in sentence:
    adverb = random.choice(words.adverbs)
    sentence = sentence.replace("adverb", adverb.capitalize(), 1)

  while "noun" in sentence and len(nouns) > 0:

    noun = random.choice(nouns)
    tags.append(noun)
    nouns.remove(noun)
    sentence = sentence.replace("noun", noun.capitalize(), 1)

  while "adjective" in sentence and len(adjectives) > 0:
    adjective = random.choice(adjectives)
    tags.append(adjective)
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
    sentence = sentence.replace("exclamations", exclamation)

  while "number" in sentence:
    sentence = sentence.replace("number", str(number_of_images), 1)

  while "years" in sentence:
    number = random.choice(words.years)
    sentence = sentence.replace("years", number, 1)

  return sentence

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
