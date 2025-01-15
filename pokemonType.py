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

# Fonction pour récupérer les types Pokémon depuis Bulbapedia
def fetch_pokemon_types():
    """Récupère la liste correcte des Pokémon types depuis Bulbapedia."""
    url = 'https://bulbapedia.bulbagarden.net/wiki/Type'
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Erreur API : {response.status_code}")
        return []

    try:
        # Parse le contenu HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Sélectionne le tableau qui contient les types
        type_box = soup.find('table', {'class': 'roundy'}).find_all('a')

        # Extraction des noms des types
        types = [a.text.strip() for a in type_box if a.text.strip()]

        # Filtrage pour éviter les entrées non valides
        valid_types = list(set(types))  # Suppression des doublons

        print(f"✅ Types Pokémon trouvés : {valid_types}")  # Debug
        return valid_types
    except Exception as e:
        print(f"❌ Erreur lors du parsing HTML : {e}")
        return []

# Création du fichier RDF pour les types Pokémon
def create_rdf_graph_for_types(types, vocab_graph):
    """Crée un graphe RDF contenant uniquement les types Pokémon, en respectant le vocabulaire."""
    EX = rdflib.Namespace("http://example.org/pokemon/")

    # Créer un nouveau graphe vierge
    new_graph = rdflib.Graph()
    new_graph.bind('ex', EX, override=True)

    # Récupérer l'URI de la classe PokemonType depuis le vocabulaire
    pokemon_type_class = rdflib.URIRef(EX.PokemonType)

    # Vérifier si PokemonType existe bien dans le vocabulaire
    if (pokemon_type_class, rdflib.RDF.type, rdflib.RDFS.Class) not in vocab_graph:
        print("⚠️ Attention : La classe PokemonType n'existe pas dans le vocabulaire !")
        return None  # On arrête ici pour éviter des incohérences

    for p_type in types:
        entity = rdflib.URIRef(EX + re.sub(r'[^\w\s-]', '', p_type).replace(' ', '_'))

        # Ajouter l'information au graphe (uniquement les types)
        new_graph.add((entity, rdflib.RDF.type, pokemon_type_class))
        new_graph.add((entity, rdflib.RDFS.label, rdflib.Literal(p_type)))

        print(f"🟢 Ajout du type : {p_type}")

    return new_graph

# Exécution des étapes
vocab_graph = load_vocabulary()
pokemon_types = fetch_pokemon_types()

if pokemon_types:
    rdf_graph = create_rdf_graph_for_types(pokemon_types, vocab_graph)

    if rdf_graph:
        # Sauvegarde uniquement des types Pokémon dans "pokemonTypes.ttl"
        ttl_file_path = "pokemonTypes.ttl"

        try:
            rdf_graph.serialize(destination=ttl_file_path, format="turtle", encoding="utf-8")
            print(f"✅ Fichier Turtle mis à jour avec uniquement les types Pokémon : {ttl_file_path}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde du fichier Turtle : {e}")
