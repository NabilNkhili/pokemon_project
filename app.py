from flask import Flask, render_template, request
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS
import re
import requests
from flask import Response  # ✅ Correct
import time


app = Flask(__name__)

from flask import Flask, Response, request
import requests

app = Flask(__name__)

@app.route('/proxy-image/')
def proxy_image():
    """Télécharge et sert l'image en évitant le blocage de Bulbapedia."""
    image_url = request.args.get("url")
    if not image_url:
        return "No image URL provided", 400

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }  # 🔥 Imitation d'un vrai navigateur

    try:
        response = requests.get(image_url, headers=headers, stream=True)
        if response.status_code == 200:
            flask_response = Response(response.content, content_type=response.headers['Content-Type'])
            flask_response.headers["Access-Control-Allow-Origin"] = "*"
            return flask_response
        return "Image not found", 404
    except requests.RequestException as e:
        return "Image not found", 404




# Load the RDF graph
EX = Namespace("http://example.org/pokemon/")
NS1 =  Namespace("http://dbpedia.org/property/")
EP = Namespace("http://example.org/episodes/")

DBP = Namespace("http://dbpedia.org/property/")
SCHEMA = Namespace("http://schema.org/")

g = Graph()
g.parse("tsv_merged_output.ttl", format="turtle")

# Définition des catégories pour tout afficher
categories = {
    "pokemon": EX.Pokemon,
    "move": EX.Move,
    "item": EX.Item,
    "ability": EX.Ability,
    "Type": EX.PokemonType,
    "egg-group": EX.EggGroup,
    "episode": EP.Episode,
    "game": EX.Game,
    "character": EX.Character
}


# HOMEPAGE: Display categories
@app.route("/")
def home():
    return render_template("home.html", categories=categories)


# CATEGORY PAGE: List all entities within a category
@app.route("/category/<category>")
def category(category):
    query = request.args.get("query", "").lower()
    results = []
    
    if category in categories:
        for s in g.subjects(RDF.type, categories[category]):
            label = g.value(s, RDFS.label)
            
            if category.lower() in ["type", "egg-group"]:
                # Pour la catégorie "Type", on ne récupère que le label
                results.append({"label": label})
            else:
                # Pour les autres catégories, on récupère l'image et le lien
                image = g.value(s, EX.hasImage, default="/static/no_image.png")
                if not query or (label and query in label.lower()):
                    results.append({"uri": str(s), "label": label, "image": image})
                    
    else:
        return f"Category '{category}' not found.", 404

    return render_template("category.html", results=results, category=category.capitalize())


# Fonction pour rendre les prédicats plus lisibles
def format_predicate(predicate):
    # Remplacer les prédicats RDF par des termes plus lisibles
    if predicate == str(RDFS.label):
        return "Label"
    elif predicate == str(RDF.type):
        return "Type"
    
    # Gestion générale des autres prédicats (supprimer "has" et formater)
    clean_predicate = predicate.split("/")[-1]
    if clean_predicate.lower().startswith("has"):
        clean_predicate = clean_predicate[3:]
    return clean_predicate.replace("_", " ").capitalize()

# DETAILS PAGE: Show details for a specific Pokémon
@app.route("/pokemon/<pokemon_name>")
def pokemon_details(pokemon_name):
    EX = Namespace("http://example.org/pokemon/")
    NS1 = Namespace("http://dbpedia.org/property/")
    SCHEMA = Namespace("http://schema.org/")  # Ajoutez ce namespace si nécessaire
    pokemon_uri = EX[pokemon_name.replace(' ', '_')]
    
    label = g.value(pokemon_uri, RDFS.label)
    image = g.value(pokemon_uri, EX.hasImage, default="/static/no_image.png")
    
    # Fetch URIs and then their labels
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
    
     # Récupérer les noms dans différentes langues
    names = {}
    for name in g.objects(pokemon_uri, SCHEMA.name):
        lang = name.language  # Récupérer la langue du nom
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
        "names": names  # Ajouter les noms multilingues

    }
    
    return render_template("pokemon_details.html", details=details)

@app.route("/category/ability")
def list_abilities():
    EX = Namespace("http://example.org/pokemon/")
    NS1 = Namespace("http://dbpedia.org/property/")

    abilities = []
    hidden_abilities = []

    # Récupérer toutes les instances de ex:Ability
    for ability_uri in g.subjects(RDF.type, EX.Ability):
        label = g.value(ability_uri, RDFS.label)
        if label:
            is_hidden = any(g.triples((None, NS1.hasHiddenAbility, ability_uri)))
            if is_hidden:
                hidden_abilities.append({"uri": str(ability_uri), "label": label})
            else:
                abilities.append({"uri": str(ability_uri), "label": label})
    # Compter le nombre total de capacités
    total_abilities = len(abilities) + len(hidden_abilities)

    return render_template("abilities.html", abilities=abilities,
        hidden_abilities=hidden_abilities,
        total_abilities=total_abilities)
    
@app.route("/ability/<ability_name>")
def ability_details(ability_name):
    EX = Namespace("http://example.org/pokemon/")
    SCHEMA = Namespace("http://example.org/schema/")  # Namespace personnalisé pour les propriétés
    
    # Convertir le nom de la capacité en URI
    ability_uri = EX[ability_name.replace(' ', '_')]
    
    # Récupérer les informations de la capacité depuis le graphe RDF
    label = g.value(ability_uri, RDFS.label)
    details = {}

    # Récupérer les propriétés de la capacité
    for p, o in g.predicate_objects(ability_uri):
        if str(p).startswith(str(SCHEMA)):  # Filtrer les propriétés personnalisées
            key = str(p).split('/')[-1]  # Extraire le nom de la propriété
            details[key] = str(o)

    # Préparer les données pour le template
    ability_info = {
        "label": label,
        "details": details
    }

    return render_template("ability_details.html", ability=ability_info)  
@app.route("/type")
def list_types():
    EX = Namespace("http://example.org/pokemon/")
    types = []

    # Récupérer toutes les instances de ex:PokemonType
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

    # Recherche limitée à la catégorie actuelle
    if category in categories:
        for s, p, o in g.triples((None, RDFS.label, None)):
            if query.lower() in str(o).lower() and (s, RDF.type, categories[category]) in g:
                results.append({"uri": str(s), "label": o})
    # Si aucune catégorie n'est spécifiée, effectuer une recherche globale
    else:
        for s, p, o in g.triples((None, RDFS.label, None)):
            if query.lower() in str(o).lower():
                results.append({"uri": str(s), "label": o})

    return render_template("search_results.html", results=results, category=category)





if __name__ == "__main__":
    app.run(debug=True)
