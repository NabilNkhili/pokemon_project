from flask import Flask, render_template, request
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS
import re
import requests
from flask import Response 
import time
import os




from flask import Flask, Response, request
import requests

app = Flask(__name__)


CACHE_DIR = "static/cache"

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


import os
from flask import Flask, request, send_file, Response
import requests

app = Flask(__name__)

CACHE_DIR = "static/cache"

# Créez le dossier cache s'il n'existe pas
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

@app.route('/proxy-image/')
def proxy_image():
    """Télécharge et sert l'image en évitant le blocage de Bulbapedia."""
    image_url = request.args.get("url")
    if not image_url:
        return "No image URL provided", 400

    # Générer un nom de fichier basé sur l'URL
    image_filename = os.path.join(CACHE_DIR, os.path.basename(image_url))
    
    # Si le fichier existe déjà en cache, le servir directement
    if os.path.exists(image_filename):
        return send_file(image_filename, mimetype="image/png")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }  #Imitation d'un vrai navigateur

    try:
        response = requests.get(image_url, headers=headers, stream=True)
        if response.status_code == 200:
            # Enregistrer l'image localement
            with open(image_filename, "wb") as f:
                f.write(response.content)
            
            return send_file(image_filename, mimetype="image/png")
        return "Image not found", 404
    except requests.RequestException:
        return "Image not found", 404





EX = Namespace("http://example.org/pokemon/")
NS1 =  Namespace("http://dbpedia.org/property/")
EP = Namespace("http://example.org/episodes/")
CH = Namespace("http://example.org/characters/")
IT = Namespace("http://example.org/items/")
DBP = Namespace("http://dbpedia.org/property/")
SCHEMA = Namespace("http://schema.org/")

g = Graph()
g.parse("KG.ttl", format="turtle")

categories = {
    "pokemon": EX.Pokemon,
    "move": EX.Move,
    "item": IT.Item,
    "ability": EX.Ability,
    "Type": EX.PokemonType,
    "egg-group": EX.EggGroup,
    "episode": EP.Episode,
    "game": EX.Game,
    "character": CH.Character
}


@app.route("/")
def home():
    return render_template("home.html", categories=categories)


@app.route("/category/<category>")
def category(category):
    query = request.args.get("query", "").lower()
    results = []
    
    if category in categories:
        for s in g.subjects(RDF.type, categories[category]):
            label = g.value(s, RDFS.label)
            
            if category.lower() in ["type", "egg-group"]:
                results.append({"label": label})
            elif category.lower() == "move":
                for s in g.subjects(RDF.type, categories[category]):
                    label = g.value(s, RDFS.label)
                    image = g.value(s, SCHEMA.image, default="/static/no_image.png")
                    if not query or (label and query in label.lower()):
                        results.append({"uri": str(s), "label": label, "image": image})
            elif category.lower() == "episode":
                image = g.value(s, EP.hasImage, default="/static/no_image.png")
                title = g.value(s, EP.hasTitle)
                if not query or (title and query in title.lower()):
                    results.append({"uri": str(s), "label": title, "image": image})
                    
            elif category.lower() == "game":
                image = g.value(s, SCHEMA.imageURL, default="/static/no_image.png")
                if not query or (label and query in label.lower()):
                    results.append({"uri": str(s), "label": label, "image": image})
                    
            elif category.lower() == "character":
                image = g.value(s, SCHEMA.Image, default="/static/no_character.png")
                if not query or (label and query in label.lower()):
                    results.append({"uri": str(s), "label": label, "image": image})
               
            elif category.lower() == "item":
                image = g.value(s, SCHEMA.Image, default="/static/no_item.png")
                introduced_in = g.value(s, SCHEMA.IntroducedIn, default="Unknown")
                if not query or (label and query in label.lower()):
                    results.append({
                        "uri": str(s),
                        "label": label,
                        "image": image,
                        "introduced_in": introduced_in
                    })                
            else:
                image = g.value(s, EX.hasImage, default="/static/no_image.png")
                if not query or (label and query in label.lower()):
                    results.append({"uri": str(s), "label": label, "image": image})
                    
    else:
        return f"Category '{category}' not found.", 404

    return render_template("category.html", results=results, category=category.capitalize())


@app.route("/item/<item_name>")
def item_details(item_name):
    """Affiche les détails d'un item."""
    item_uri = None
    for s in g.subjects(RDF.type, IT.Item):
        label = g.value(s, RDFS.label)
        if label and label.lower() == item_name.lower():
            item_uri = s
            break

    if not item_uri:
        return "Item not found", 404

    details = {
        "label": g.value(item_uri, RDFS.label),
        "image": g.value(item_uri, SCHEMA.Image, default="/static/no_image.png"),
        "introduced_in": g.value(item_uri, SCHEMA.IntroducedIn, default="Unknown"),
        "artwork": g.value(item_uri, SCHEMA.Artwork, default="Unknown"),
        "power": g.value(item_uri, SCHEMA.Power, default="Unknown"),
        "generations": {
            predicate.split("_")[-1]: g.value(item_uri, SCHEMA[predicate])
            for predicate in ["Generation_V", "Generation_VI", "Generation_VII", "Generation_VIII", "Generation_IX"]
            if g.value(item_uri, SCHEMA[predicate])
        }
    }

    return render_template("item_details.html", details=details)

@app.route("/character/<character_name>")
def character_details(character_name):
    character_uri = None
    for s in g.subjects(RDF.type, CH.Character):
        label = g.value(s, RDFS.label)
        if label and label.lower() == character_name.lower():
            character_uri = s
            break

    if not character_uri:
        return "Character not found", 404

    details = {
        "label": g.value(character_uri, RDFS.label),
        "gender": g.value(character_uri, SCHEMA.Gender),
        "region": g.value(character_uri, SCHEMA.Region),
        "trainer_class": g.value(character_uri, SCHEMA.Trainer_class),
        "hometown": g.value(character_uri, SCHEMA.Hometown),
        "generation": g.value(character_uri, SCHEMA.Generation),
        "specializes_in": g.value(character_uri, SCHEMA.Specializes_in),
        "games": g.objects(character_uri, SCHEMA.Games),
        "image": g.value(character_uri, SCHEMA.Image, default="/static/no_character.png"),
    }

    return render_template("character_details.html", details=details)


@app.route("/game/<game_name>")
def game_details(game_name):
    game_uri = None
    for s in g.subjects(RDF.type, EX.Game):
        label = g.value(s, RDFS.label)
        if label and label.lower() == game_name.lower():
            game_uri = s
            break

    if not game_uri:
        return "Game not found", 404

    details = {
        "label": g.value(game_uri, RDFS.label),
        "category": g.value(game_uri, SCHEMA.Category),
        "platform": g.value(game_uri, SCHEMA.Platform),
        "players": g.value(game_uri, SCHEMA.Players),
        "connectivity": g.value(game_uri, SCHEMA.Connectivity),
        "developer": g.value(game_uri, SCHEMA.Developer),
        "publisher": g.value(game_uri, SCHEMA.Publisher),
        "part_of": g.value(game_uri, SCHEMA.Part_of),
        "release_dates": {
            "Japan": g.value(game_uri, SCHEMA.releaseDate_Japan),
            "North America": g.value(game_uri, SCHEMA.releaseDate_North_America),
            "Australia": g.value(game_uri, SCHEMA.releaseDate_Australia),
            "Europe": g.value(game_uri, SCHEMA.releaseDate_Europe),
            "South Korea": g.value(game_uri, SCHEMA.releaseDate_South_Korea),
            "Hong Kong": g.value(game_uri, SCHEMA.releaseDate_Hong_Kong),
            "Taiwan": g.value(game_uri, SCHEMA.releaseDate_Taiwan),
        },
        "image": g.value(game_uri, SCHEMA.imageURL, default="/static/no_image.png"),
    }

    return render_template("game_details.html", details=details)


@app.route("/move/<move_name>")
def move_details(move_name):
    move_uri = None
    for s in g.subjects(RDF.type, EX.Move):
        label = g.value(s, RDFS.label)
        if label and label.lower() == move_name.lower():
            move_uri = s
            break
    
    if not move_uri:
        return "Move not found", 404
    
    type_uri = g.value(move_uri, EX.hasType)
    type_label = g.value(type_uri, RDFS.label) if type_uri else None

    details = {
        "label": g.value(move_uri, RDFS.label),
        "type": type_label,
        "accuracy": g.value(move_uri, SCHEMA.accuracy),
        "category": g.value(move_uri, SCHEMA.category),
        "image": g.value(move_uri, SCHEMA.image, default="/static/no_image.png"),
        "power": g.value(move_uri, SCHEMA.power),
        "pp": g.value(move_uri, SCHEMA.pp),
    }
    
    return render_template("move_details.html", details=details)


@app.route("/episode/<episode_id>")
def episode_details(episode_id):
    episode_uri = None
    for s in g.subjects(RDF.type, EP.Episode):
        title = g.value(s, EP.hasTitle)
        if title and title.lower() == episode_id.lower():
            episode_uri = s
            break

    if not episode_uri:
        return "Episode not found", 404

    details = {
        "title": g.value(episode_uri, EP.hasTitle),
        "image": g.value(episode_uri, EP.hasImage, default="/static/no_image.png"),
        "episode_number": g.value(episode_uri, EP.hasEpisodeNumber),
        "japan_release_date": g.value(episode_uri, EP.hasJapanReleaseDate),
        "us_release_date": g.value(episode_uri, EP.hasUSReleaseDate),
        "director": g.value(episode_uri, EP.hasDirector),
        "screenplay": g.value(episode_uri, EP.hasScreenplay),
        "storyboard": g.value(episode_uri, EP.hasStoryboard),
        "opening": g.value(episode_uri, EP.hasOpening),
        "ending": g.value(episode_uri, EP.hasEnding),
        "animation": g.value(episode_uri, EP.hasAnimation),
        "pokemon_debut": [
            {
                "label": g.value(pokemon, RDFS.label) or None,
                "image": g.value(pokemon, EX.hasImage, default=None)
            }
            for pokemon in g.objects(episode_uri, EP.hasPokemonDebut)
            if g.value(pokemon, RDFS.label)  # Assure qu'un label existe
        ],
    }

    return render_template("episode_details.html", details=details)

def format_predicate(predicate):
    if predicate == str(RDFS.label):
        return "Label"
    elif predicate == str(RDF.type):
        return "Type"
    
    clean_predicate = predicate.split("/")[-1]
    if clean_predicate.lower().startswith("has"):
        clean_predicate = clean_predicate[3:]
    return clean_predicate.replace("_", " ").capitalize()


@app.route("/pokemon/<pokemon_name>")
def pokemon_details(pokemon_name):
    EX = Namespace("http://example.org/pokemon/")
    NS1 = Namespace("http://dbpedia.org/property/")
    SCHEMA = Namespace("http://schema.org/")  
    pokemon_uri = EX[pokemon_name.replace(' ', '_')]
    
    label = g.value(pokemon_uri, RDFS.label)
    image = g.value(pokemon_uri, EX.hasImage, default="/static/no_image.png")
    
    abilities = list(g.objects(pokemon_uri, NS1.hasAbility))
    ability_labels = []
    for ability_uri in abilities:
        ability_label = g.value(ability_uri, RDFS.label)
        if ability_label:
            ability_labels.append(ability_label)
        else:
            ability_labels.append(str(ability_uri))
    
    egg_groups = list(g.objects(pokemon_uri, NS1.hasEggGroup))
    egg_group_labels = []
    for egg_group_uri in egg_groups:
        egg_group_label = g.value(egg_group_uri, RDFS.label)
        if egg_group_label:
            egg_group_labels.append(egg_group_label)
        else:
            egg_group_labels.append(str(egg_group_uri))
    
    types = list(g.objects(pokemon_uri, NS1.hasType))
    type_labels = []
    for type_uri in types:
        type_label = g.value(type_uri, RDFS.label)
        if type_label:
            type_labels.append(type_label)
        else:
            type_labels.append(str(type_uri))
    
    hidden_ability_uri = g.value(pokemon_uri, NS1.hasHiddenAbility)
    hidden_ability_label = g.value(hidden_ability_uri, RDFS.label) if hidden_ability_uri else "None"
    
    category = g.value(pokemon_uri, EX.category)
    color = g.value(pokemon_uri, EX.color)
    friendship = g.value(pokemon_uri, EX.friendship)
    hatchtime = g.value(pokemon_uri, EX.hatchtime)
    height = g.value(pokemon_uri, EX.height)
    jname = g.value(pokemon_uri, EX.jname)
    ndex = g.value(pokemon_uri, EX.ndex)
    weight = g.value(pokemon_uri, EX.weight)
    
    names = {}
    for name in g.objects(pokemon_uri, SCHEMA.name):
        lang = name.language 
        names[lang] = str(name)
        
    details = {
        "label": label,
        "image": image,
        "abilities": ability_labels,
        "egg_groups": egg_group_labels,
        "hidden_ability": hidden_ability_label,
        "types": type_labels,
        "category": category,
        "color": color,
        "friendship": friendship,
        "hatchtime": hatchtime,
        "height": height,
        "jname": jname,
        "ndex": ndex,
        "weight": weight,
        "names": names  

    }
    
    return render_template("pokemon_details.html", details=details)

@app.route("/category/ability")
def list_abilities():
    EX = Namespace("http://example.org/pokemon/")
    NS1 = Namespace("http://dbpedia.org/property/")

    abilities = []
    hidden_abilities = []

    for ability_uri in g.subjects(RDF.type, EX.Ability):
        label = g.value(ability_uri, RDFS.label)
        if label:
            is_hidden = any(g.triples((None, NS1.hasHiddenAbility, ability_uri)))
            if is_hidden:
                hidden_abilities.append({"uri": str(ability_uri), "label": label})
            else:
                abilities.append({"uri": str(ability_uri), "label": label})
    total_abilities = len(abilities) + len(hidden_abilities)

    return render_template("abilities.html", abilities=abilities,
        hidden_abilities=hidden_abilities,
        total_abilities=total_abilities)
    
@app.route("/ability/<ability_name>")
def ability_details(ability_name):
    EX = Namespace("http://example.org/pokemon/")
    SCHEMA = Namespace("http://example.org/schema/")  
    
    ability_uri = EX[ability_name.replace(' ', '_')]
    
    label = g.value(ability_uri, RDFS.label)
    details = {}

    for p, o in g.predicate_objects(ability_uri):
        if str(p).startswith(str(SCHEMA)):  
            key = str(p).split('/')[-1] 
            details[key] = str(o)

    ability_info = {
        "label": label,
        "details": details
    }

    return render_template("ability_details.html", ability=ability_info)  
@app.route("/type")
def list_types():
    EX = Namespace("http://example.org/pokemon/")
    types = []

    for type_uri in g.subjects(RDF.type, EX.PokemonType):
        label = g.value(type_uri, RDFS.label)
        if label:
            types.append({"uri": str(type_uri), "label": label})

    return render_template("types.html", types=types)

@app.route("/search")
def search():
    query = request.args.get("query")
    category = request.args.get("category")
    results = []

    if category in categories:
        for s, p, o in g.triples((None, RDFS.label, None)):
            if query.lower() in str(o).lower() and (s, RDF.type, categories[category]) in g:
                results.append({"uri": str(s), "label": o})
    else:
        for s, p, o in g.triples((None, RDFS.label, None)):
            if query.lower() in str(o).lower():
                results.append({"uri": str(s), "label": o})

    return render_template("search_results.html", results=results, category=category)





if __name__ == "__main__":
    app.run(debug=True)
