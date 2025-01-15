import requests
import rdflib
import re
import time
from rdflib import XSD  # Import du namespace XSD
from flask import Flask

app = Flask(__name__)


def get_actual_image_url(ndex, pokemon_name):
    """Récupère l'URL directe de l'image à partir de la page Bulbapedia."""
    
    pokemon_name_clean = clean_pokemon_name(pokemon_name)
    file_page_url = f"https://bulbapedia.bulbagarden.net/wiki/File:{ndex}{pokemon_name_clean}.png"

    try:
        headers = {"User-Agent": "Mozilla/5.0"}  # Éviter les blocages d'accès
        response = requests.get(file_page_url, headers=headers)
        
        if response.status_code == 200:
            # Extraire l'URL réelle de l'image (présente sous 'fullImageLink' dans la page)
            match = re.search(r'//archives\.bulbagarden\.net/media/upload/[\w/]+/\d+\w+\.png', response.text)
            
            if match:
                image_url = "https:" + match.group(0)
                print(f"✅ URL trouvée : {image_url}")
                return image_url
            else:
                print(f"⚠️ Impossible de récupérer l'image pour {pokemon_name}")
                return None
        else:
            print(f"❌ Erreur en accédant à {file_page_url}: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"❌ Erreur réseau : {e}")
        return None

# Chargement des fichiers RDF existants
types_graph = rdflib.Graph()
abilities_graph = rdflib.Graph()
egg_groups_graph = rdflib.Graph()
vocab_graph = rdflib.Graph()

types_graph.parse("./data/pokemonTypes.ttl", format="turtle")
abilities_graph.parse("./data/pokemonAbilities.ttl", format="turtle")
egg_groups_graph.parse("./data/egg_groups.ttl", format="turtle")
vocab_graph.parse("./data/vocabulary_demo.ttl", format="turtle")

# Définition des namespaces
SCHEMA = rdflib.Namespace("http://schema.org/")
EX = rdflib.Namespace("http://example.org/pokemon/")
DBR = rdflib.Namespace("http://dbpedia.org/resource/")
RDFS = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")
DBP = rdflib.Namespace("http://dbpedia.org/property/")

def fetch_pokemon_list_from_api():
    """Récupère tous les Pokémon en paginant l'API de Bulbapedia."""
    url = 'https://bulbapedia.bulbagarden.net/w/api.php'
    params = {
        'action': 'query',
        'list': 'categorymembers',
        'cmtitle': 'Category:Pokémon',
        'cmlimit': '50',  # Limite par requête
        'format': 'json'
    }
    
    all_pokemon = []
    cont_flag = True
    continue_params = {}

    while cont_flag:  # Boucle pour récupérer tous les Pokémon en plusieurs requêtes
        response = requests.get(url, params={**params, **continue_params})
        if response.status_code != 200:
            print(f"❌ Erreur API : {response.status_code}")
            return []

        data = response.json()
        if 'query' in data:
            pages = [page['title'] for page in data['query']['categorymembers']]
            filtered_pages = [page for page in pages if '(Pokémon)' in page]
            all_pokemon.extend(filtered_pages)
        
        # Vérifie s'il y a une pagination (continue)
        if 'continue' in data:
            continue_params = data['continue']
        else:
            cont_flag = False  # Sort de la boucle si plus de pages

    return all_pokemon


import time

def fetch_bulbapedia_page(page_title):
    """Récupère le contenu d'une page Bulbapedia avec délai."""
    url = 'https://bulbapedia.bulbagarden.net/w/api.php'
    params = {
        'action': 'parse',
        'page': page_title,
        'format': 'json',
        'prop': 'wikitext',
        'redirects': '1'
    }

    try:
        response = requests.get(url, params=params, timeout=10)  # Ajout d'un timeout
        time.sleep(0.1)  # Délai de 0.5 secondes entre les requêtes
        if response.status_code == 200:
            data = response.json()
            wikitext = data['parse']['wikitext']['*']
            return wikitext
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau pour {page_title}: {e}")
    
    return None

    

def extract_infobox_data(wikitext):
    """Extrait toutes les informations de l'infobox Pokémon."""
    infobox_data = {}

    infobox_match = re.search(r'\{\{\s*Pokémon Infobox\s*([\s\S]*?)\n\}\}', wikitext)
    
    if infobox_match:
        infobox_text = infobox_match.group(1)
        fields = re.findall(r'\|\s*(\w+[-\w]*)\s*=\s*(.*?)(?=\n\||\n*\}\}|\n*$)', infobox_text, re.DOTALL)
        
        for key, value in fields:
            clean_value = re.sub(r'\[\[.*?\||\[\[|\]\]', '', value).strip()
            clean_value = re.sub(r'<.*?>', '', clean_value).strip()
            clean_value = re.sub(r'\{.*?\}', '', clean_value).strip()
            infobox_data[key.strip().lower()] = clean_value

        # Extraire l'image principale et alternative
        image_match = re.search(r'\|\s*image\s*=\s*(.*?)(?=\n\||\n*\}\})', wikitext)
        if image_match:
            infobox_data['image'] = image_match.group(1).strip()

        # Vérifier une autre image (ex: méga-évolution)
        image2_match = re.search(r'\|\s*image2\s*=\s*(.*?)(?=\n\||\n*\}\})', wikitext)
        if image2_match:
            infobox_data['image2'] = image2_match.group(1).strip()
            
        print(f"✅ Infobox détectée pour ce Pokémon")
        print(infobox_data)
    else:
        print("❌ Aucune infobox trouvée.")
    
    return infobox_data

def clean_pokemon_name(name):
    """Nettoie le nom d'un Pokémon ou d'une propriété pour une utilisation en URI."""
    name = re.sub(r'\(Pokémon\)', '', name).strip()
    name = re.sub(r'[^\w\s-]', '', name).replace(' ', '_')
    return name


def create_pokemon_rdf(pokemon_name, infobox_data):
    """
    Crée un graphe RDF pour un Pokémon en respectant les définitions
    et relations du vocabulaire RDF (vocabulary_demo.ttl).
    """
    g = rdflib.Graph()
    g.bind("dbp", DBP, override=True)  # Propriétés du namespace DBpedia
    g.bind("ex", EX, override=True)    # Classes et entités spécifiques au namespace EX

    # Définir l'entité Pokémon
    entity_name = clean_pokemon_name(pokemon_name)
    entity = rdflib.URIRef(EX + entity_name)  # Entité Pokémon sous EX
    g.add((entity, rdflib.RDF.type, EX.Pokemon))
    g.add((entity, RDFS.label, rdflib.Literal(pokemon_name)))
    
    # Ajouter les nouvelles informations
    if 'jname' in infobox_data:
        g.add((entity, EX.jname, rdflib.Literal(infobox_data['jname'], datatype=XSD.string)))
    if 'category' in infobox_data:
        g.add((entity, EX.category, rdflib.Literal(infobox_data['category'], datatype=XSD.string)))
    if 'ndex' in infobox_data:
        g.add((entity, EX.ndex, rdflib.Literal(infobox_data['ndex'], datatype=XSD.string)))
    if 'color' in infobox_data:
        g.add((entity, EX.color, rdflib.Literal(infobox_data['color'], datatype=XSD.string)))
    if 'friendship' in infobox_data:
        g.add((entity, EX.friendship, rdflib.Literal(infobox_data['friendship'], datatype=XSD.integer)))
            
    # Ajouter height, weight, et hatchtime
    if 'height-m' in infobox_data:
        try:
            height_value = float(infobox_data['height-m'])
            g.add((entity, EX.height, rdflib.Literal(height_value, datatype=XSD.decimal)))
        except ValueError:
            print(f"⚠️ Valeur de hauteur invalide pour {pokemon_name}: {infobox_data['height-m']}")

    if 'weight-kg' in infobox_data:
        try:
            weight_value = float(infobox_data['weight-kg'])
            g.add((entity, EX.weight, rdflib.Literal(weight_value, datatype=XSD.decimal)))
        except ValueError:
            print(f"⚠️ Valeur de poids invalide pour {pokemon_name}: {infobox_data['weight-kg']}")

    if 'eggcycles' in infobox_data:
        hatchtime_value = infobox_data['eggcycles'].strip()
        g.add((entity, EX.hatchtime, rdflib.Literal(hatchtime_value, datatype=XSD.string)))
        
    
   

    # 1️⃣ **Ajouter les types**
    if "type1" in infobox_data or "type2" in infobox_data:
        types_list = [infobox_data.get("type1"), infobox_data.get("type2")]
        for t in types_list:
            if t:
                type_uri = rdflib.URIRef(EX + clean_pokemon_name(t))  # Type sous EX
                if (type_uri, rdflib.RDF.type, EX.PokemonType) in types_graph:
                    g.add((entity, DBP.hasType, type_uri))  # Propriété sous DBP
                    print(f"✅ Type ajouté pour {pokemon_name} : {t}")
                else:
                    print(f"⚠️ Type non trouvé dans types.ttl : {t}")

    # 2️⃣ **Ajouter les abilities**
    if "ability1" in infobox_data or "ability2" in infobox_data:
        abilities_list = [infobox_data.get("ability1"), infobox_data.get("ability2")]
        for ab in abilities_list:
            if ab:
                ability_uri = rdflib.URIRef(EX + clean_pokemon_name(ab))  # Ability sous EX
                if (ability_uri, rdflib.RDF.type, EX.Ability) in abilities_graph:
                    g.add((entity, DBP.hasAbility, ability_uri))  # Propriété sous DBP
                    print(f"✅ Ability ajoutée pour {pokemon_name} : {ab}")
                else:
                    print(f"⚠️ Ability non trouvée dans abilities_all.ttl : {ab}")

        # Ajouter Hidden Ability (même si absente)
    if "abilityd" in infobox_data and infobox_data["abilityd"].strip():
        hidden_ability = infobox_data["abilityd"]
        hidden_ability_uri = rdflib.URIRef(EX + clean_pokemon_name(hidden_ability))

    # Vérifier si l'ability existe déjà sinon l'ajouter
        if (hidden_ability_uri, rdflib.RDF.type, EX.HiddenAbility) not in abilities_graph:
            g.add((hidden_ability_uri, rdflib.RDF.type, EX.Ability))
            g.add((hidden_ability_uri, rdflib.RDF.type, EX.HiddenAbility))
            print(f"🔹 Hidden Ability ajoutée manuellement : {hidden_ability}")

        g.add((entity, DBP.hasHiddenAbility, hidden_ability_uri))
        print(f"✅ Hidden Ability liée à {pokemon_name} : {hidden_ability}")
    else:
        print(f"ℹ️ {pokemon_name} n'a pas de Hidden Ability")

    
    # 3️⃣ **Ajouter les egg groups**
    if "egggroup1" in infobox_data or "egggroup2" in infobox_data:
        egg_groups_list = [infobox_data.get("egggroup1"), infobox_data.get("egggroup2")]
        for eg in egg_groups_list:
            if eg:
                egg_group_uri = rdflib.URIRef(EX + clean_pokemon_name(eg))  # Egg Group sous EX
                if (egg_group_uri, rdflib.RDF.type, EX.EggGroup) in egg_groups_graph:
                    g.add((entity, DBP.hasEggGroup, egg_group_uri))  # Propriété sous DBP
                    print(f"✅ Egg Group ajouté pour {pokemon_name} : {eg}")
                else:
                    print(f"⚠️ Egg Group non trouvé dans egg_groups.ttl : {eg}")

    # ✅ Ajouter l'URL de l'image à RDF
    if 'image_rdf' in infobox_data:
        image_uri = rdflib.Literal(infobox_data['image_rdf'], datatype=XSD.anyURI)
        g.add((entity, EX.hasImage, image_uri))
        print(f"✅ Image ajoutée au RDF pour {pokemon_name}: {infobox_data['image_rdf']}")
        
    return g




def main():
    all_pokemon = fetch_pokemon_list_from_api()
    rdf_graph = rdflib.Graph()

    rdf_graph.bind('schema', SCHEMA, override=True)
    rdf_graph.bind('ex', EX, override=True)

    total_pokemon_traites = 0
    max_pokemon = 1500  # Limite de Pokémon à traiter


    for pokemon_name in all_pokemon:
        if total_pokemon_traites >= max_pokemon:
            break  # Arrête la boucle après avoir traité 10 Pokémon

        wikitext = fetch_bulbapedia_page(pokemon_name)

        if not wikitext:
            print(f"❌ Aucune donnée trouvée pour : {pokemon_name}.")
            continue  

        infobox_data = extract_infobox_data(wikitext)
        
        if not infobox_data:
            print(f"❌ Infobox introuvable pour {pokemon_name}.")
            continue  


        image_rdf = get_actual_image_url(infobox_data.get('ndex', '0000'), pokemon_name)

        # ✅ Ajouter l'URL correcte dans le RDF
        if image_rdf:
            infobox_data['image_rdf'] = image_rdf


        graph = create_pokemon_rdf(pokemon_name, infobox_data)
        rdf_graph += graph
        total_pokemon_traites += 1
        print(f"✅ Pokémon traité : {pokemon_name}")

    rdf_graph.serialize(destination="all_pokemon.ttl", format="turtle", encoding="utf-8")
    print(f"✅ Fichier RDF généré avec succès : all_pokemon.ttl")
    print(f"🔹 Nombre total de Pokémon traités : {total_pokemon_traites}")



if __name__ == "__main__":
    main()
