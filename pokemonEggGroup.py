import requests
import rdflib
import re
from bs4 import BeautifulSoup

# Chargement du vocabulaire RDF existant
VOCAB_FILE = "vocabulary_demo.ttl"

def load_vocabulary():
    """Charge le vocabulaire RDF existant."""
    g = rdflib.Graph()
    try:
        g.parse(VOCAB_FILE, format="turtle")
        print("✅ Vocabulaire chargé avec succès.")
    except Exception as e:
        print(f"❌ Erreur lors du chargement du vocabulaire : {e}")
    return g

# Fonction pour récupérer les Egg Groups depuis Bulbapedia
def fetch_egg_groups():
    url = "https://bulbapedia.bulbagarden.net/wiki/Egg_Group"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Erreur API : {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extraction des Egg Groups dans le tableau
    egg_groups = []
    for item in soup.find_all("a", {"title": True}):
        title = item["title"]
        if "Egg Group" in title and title != "Egg Group":
            egg_group_name = title.replace(" (Egg Group)", "")
            egg_groups.append(egg_group_name)

    return list(set(egg_groups))  # Supprimer les doublons

# Création du graphe RDF pour les Egg Groups
def create_egg_groups_rdf(egg_groups, vocab_graph):
    """Crée un graphe RDF pour les Egg Groups en respectant le vocabulaire."""
    EX = rdflib.Namespace("http://example.org/pokemon/")
    
    # Créer un graphe vierge
    new_graph = rdflib.Graph()
    new_graph.bind("ex", EX)

    # Vérifier si la classe EggGroup existe dans le vocabulaire
    egg_group_class = rdflib.URIRef(EX.EggGroup)

    if (egg_group_class, rdflib.RDF.type, rdflib.RDFS.Class) not in vocab_graph:
        print("⚠️ Attention : La classe EggGroup n'existe pas dans le vocabulaire !")
        return None

    for egg_group in egg_groups:
        entity = rdflib.URIRef(EX + re.sub(r'[^\w\s-]', '', egg_group).replace(' ', '_'))
        new_graph.add((entity, rdflib.RDF.type, egg_group_class))
        new_graph.add((entity, rdflib.RDFS.label, rdflib.Literal(egg_group)))

        print(f"✅ Egg Group ajouté : {egg_group}")

    return new_graph

# Exécution principale
vocab_graph = load_vocabulary()
egg_groups = fetch_egg_groups()

if egg_groups:
    rdf_graph = create_egg_groups_rdf(egg_groups, vocab_graph)

    if rdf_graph:
        # Sauvegarde uniquement des Egg Groups dans "egg_groups.ttl"
        ttl_file_path = "egg_groups.ttl"

        try:
            rdf_graph.serialize(destination=ttl_file_path, format="turtle", encoding="utf-8")
            print(f"✅ Fichier Turtle mis à jour avec uniquement les Egg Groups : {ttl_file_path}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde du fichier Turtle : {e}")
