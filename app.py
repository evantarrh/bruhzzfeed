from flask import Flask, render_template, url_for, make_response, redirect, request
from imgurpython import ImgurClient
from backend import database as db
from clarifai.client import ClarifaiApi
import random, config, json, ast, operator
from topia.termextract import tag as part_of_speech
import example_data, structures, words

client_id = config.imgur_client_id
client_secret = config.imgur_client_secret

imgur = ImgurClient(client_id, client_secret)
clarifai_api = ClarifaiApi()  # assumes environment variables are set.

pos_tagger = part_of_speech.Tagger()
pos_tagger.initialize()

app = Flask(__name__)
app.config["DEBUG"] = True

@app.route("/")
def hello():
    # TEST categories
    categories = ['animals','tech','cats','dogs','funny','babies']
    return render_template("index.html", categories=categories)

def get_imgur_images(categories):
  images = []
  total_number_of_images = 5
  images_per_category = total_number_of_images / len(categories)
  for category in categories:
    images_in_category = imgur.gallery_tag(category, sort="viral", window="day").items
    random.shuffle(images_in_category)

    image_count = 0
    for image in images_in_category:
      if image_count < images_per_category:
        if image.link.split('.')[-1] in ["gif", "png", "jpg"]:
          images.append(image.link)
          image_count += 1

  return images

@app.route("/new", methods=["POST"])
def create_article():
  # get imgur images (return list of urls) ================================

  # categories = request.get_data().DO_SOME_MAGIC()

  urls = get_imgur_images(["cats"])


  # get tags for all the images ============================================

  tags = get_tags(urls)


  # figure out common tags =================================================

  common_tags = find_common_tags(tags)

  tags_to_pos = get_pos_for_tags(common_tags)

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

  title = get_title(noun_tags, plural_noun_tags, adjective_tags)

  # select images most relevant to tags ====================================


  # use the tags to build an article name ==================================


  # make database entry with article name and URLs =========================

  urlstring = db.addPage(title,
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


def get_tags(urls):
  all_tags = []
  for i in range(0, len(urls)-1):
    one_image_tags = json.dumps(clarifai_api.tag_image_urls(str(urls[i]))['results'][0]['result']['tag']['classes'])

    # json.dumps returns a string, which we have to evaluate as a list
    one_image_tags = ast.literal_eval(one_image_tags)

    # sometimes clarifai returns a list inside a list
    if type(one_image_tags[0]) is list:
      one_image_tags = one_image_tags[0]

    tuple = (one_image_tags, str(urls[i]))

    all_tags.append(tuple)

  print all_tags
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

  print tags_to_urls

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

def get_title(nouns, plural_nouns, adjectives):
  print type(structures.sentence_structures)
  sentence = random.choice(structures.sentence_structures)
  print sentence
  sentence = sentence.replace("number", "13")
  tags = []

  if "adverb" in sentence:
    adverb = random.choice(words.adverbs)
    sentence = sentence.replace("adverb", adverb, 1)

  while "noun" in sentence and len(nouns) > 0:
    print sentence
    noun = random.choice(nouns)
    tags.append(noun)
    nouns.remove(noun)
    sentence = sentence.replace("noun", noun, 1)

  while "adjective" in sentence and len(adjectives) > 0:
    adjective = random.choice(adjectives)
    tags.append(adjective)
    adjectives.remove(adjective)
    sentence = sentence.replace("adjective", adjective, 1)

  while "adjective" in sentence:
    adjective = random.choice(words.adjectives)
    sentence = sentence.replace("adjective", adjective, 1)

  while "verb" in sentence:
    verb = random.choice(words.verbs)
    sentence = sentence.replace("verb", verb, 1)

  if "exclaim" in sentence:
    exclamation = random.choice(words.exclamations)
    sentence = sentence.replace("exclaim", exclamation)

  return sentence

if __name__ == "__main__":
    app.run(host="0.0.0.0")
