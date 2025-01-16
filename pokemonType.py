import requests
import rdflib
import re
from bs4 import BeautifulSoup

VOCAB_FILE = "vocabulary_demo.ttl"

def load_vocabulary():
    """Charge le vocabulaire RDF existant."""
    g = rdflib.Graph()
    try:
        g.parse(VOCAB_FILE, format="turtle")
        print(" Vocabulaire chargé avec succès.")
    except Exception as e:
        print(f" Erreur lors du chargement du vocabulaire : {e}")
    return g

def fetch_pokemon_types():
    url = 'https://bulbapedia.bulbagarden.net/wiki/Type'
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f" Erreur API : {response.status_code}")
        return []

    try:
        soup = BeautifulSoup(response.text, 'html.parser')

        type_box = soup.find('table', {'class': 'roundy'}).find_all('a')

        types = [a.text.strip() for a in type_box if a.text.strip()]

        valid_types = list(set(types))  

        print(f" Types Pokémon trouvés : {valid_types}")  # Debug
        return valid_types
    except Exception as e:
        print(f" Erreur lors du parsing HTML : {e}")
        return []

def create_rdf_graph_for_types(types, vocab_graph):
    """Crée un graphe RDF contenant uniquement les types Pokémon, en respectant le vocabulaire."""
    EX = rdflib.Namespace("http://example.org/pokemon/")

    new_graph = rdflib.Graph()
    new_graph.bind('ex', EX, override=True)

    pokemon_type_class = rdflib.URIRef(EX.PokemonType)

    if (pokemon_type_class, rdflib.RDF.type, rdflib.RDFS.Class) not in vocab_graph:
        print("⚠️ Attention : La classe PokemonType n'existe pas dans le vocabulaire !")
        return None  

    for p_type in types:
        entity = rdflib.URIRef(EX + re.sub(r'[^\w\s-]', '', p_type).replace(' ', '_'))

        new_graph.add((entity, rdflib.RDF.type, pokemon_type_class))
        new_graph.add((entity, rdflib.RDFS.label, rdflib.Literal(p_type)))

        print(f" Ajout du type : {p_type}")

    return new_graph

vocab_graph = load_vocabulary()
pokemon_types = fetch_pokemon_types()

if pokemon_types:
    rdf_graph = create_rdf_graph_for_types(pokemon_types, vocab_graph)

    if rdf_graph:
        ttl_file_path = "pokemonTypes.ttl"

        try:
            rdf_graph.serialize(destination=ttl_file_path, format="turtle", encoding="utf-8")
            print(f" Fichier Turtle mis à jour avec uniquement les types Pokémon : {ttl_file_path}")
        except Exception as e:
            print(f" Erreur lors de la sauvegarde du fichier Turtle : {e}")
