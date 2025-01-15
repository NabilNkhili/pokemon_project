import requests
import rdflib
import re
from bs4 import BeautifulSoup

# Chargement du vocabulaire RDF existant
VOCAB_FILE = "./data/vocabulary_demo.ttl"

def load_vocabulary():
    """Charge le vocabulaire RDF existant."""
    g = rdflib.Graph()
    try:
        g.parse(VOCAB_FILE, format="turtle")
        print("✅ Vocabulaire chargé avec succès.")
    except Exception as e:
        print(f"❌ Erreur lors du chargement du vocabulaire : {e}")
    return g

# URLs Bulbapedia
BASE_URL = "https://bulbapedia.bulbagarden.net"
ABILITIES_URL = BASE_URL + "/wiki/Category:Abilities"
HIDDEN_ABILITIES_URL = BASE_URL + "/wiki/Category:Abilities_only_available_as_a_Hidden_Ability"

def fetch_all_abilities():
    """Récupère toutes les abilities depuis Bulbapedia."""
    abilities = []
    next_page_url = ABILITIES_URL

    while next_page_url:
        response = requests.get(next_page_url)
        if response.status_code != 200:
            print(f"❌ Erreur API : {response.status_code}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        abilities_links = soup.select('div.mw-category-group ul li a')

        for a in abilities_links:
            ability_name = a.text.strip().replace(" (Ability)", "")
            if not ability_name.startswith("List of") and not "Category" in ability_name:
                ability_url = BASE_URL + a['href']
                abilities.append((ability_name, ability_url))

        # Passer à la page suivante
        next_page_link = soup.find('a', string="next page")
        next_page_url = BASE_URL + next_page_link['href'] if next_page_link else None

    print(f"✅ {len(abilities)} Abilities trouvées.")
    return abilities


def fetch_hidden_abilities():
    """Récupère uniquement les Hidden Abilities depuis Bulbapedia."""
    response = requests.get(HIDDEN_ABILITIES_URL)
    if response.status_code != 200:
        print(f"❌ Erreur API Hidden Abilities : {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    hidden_abilities_list = soup.select('div.mw-category-group ul li a')
    hidden_abilities = [a.text.strip().replace(" (Ability)", "") for a in hidden_abilities_list]

    print(f"✅ {len(hidden_abilities)} Hidden Abilities trouvées.")
    return hidden_abilities

def fetch_ability_details(ability_url):
    """Extrait les détails de l'ability depuis l'infobox."""
    response = requests.get(ability_url)
    if response.status_code != 200:
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    infobox_data = {}
    infobox_table = soup.find('table', {'class': 'roundy'})

    if not infobox_table:
        return {}

    for row in infobox_table.find_all('tr'):
        header = row.find('th')
        value = row.find('td')
        
        if header and value:
            key = header.text.strip()
            value = value.text.strip().replace('\n', ' ')
            
            # Formater la clé pour qu'elle soit valide dans un URI RDF
            key = key.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
            key = key.replace('é', 'e').replace('è', 'e').replace('à', 'a')  # Supprimer les accents
            key = key.replace(':', '').replace('!', '').replace('?', '')  # Supprimer les caractères spéciaux
            
            # Gestion des effets par génération
            if "Generation" in key:
                # Extraire les effets par génération
                matches = re.findall(r'(Generation [IVXLCDM]+)(.*?)(?=Generation|\Z)', value)
                for generation, description in matches:
                    generation_key = generation.replace(' ', '_')  # Formatage pour le RDF
                    infobox_data[generation_key] = description.strip()
            else:
                # Autres informations de l'infobox
                infobox_data[key] = value.strip()

    return infobox_data


def create_rdf_graph_for_abilities(abilities, hidden_abilities, vocab_graph):
    """Crée un graphe RDF contenant uniquement les abilities, en respectant le vocabulaire."""
    EX = rdflib.Namespace("http://example.org/pokemon/")
    SCHEMA = rdflib.Namespace("http://example.org/schema/")  # Namespace personnalisé pour les propriétés

    # Créer un graphe vierge
    new_graph = rdflib.Graph()
    new_graph.bind('ex', EX, override=True)
    new_graph.bind('schema', SCHEMA, override=True)


    # Vérifier si la classe Ability et HiddenAbility existent dans le vocabulaire
    ability_class = rdflib.URIRef(EX.Ability)
    hidden_ability_class = rdflib.URIRef(EX.HiddenAbility)

    if (ability_class, rdflib.RDF.type, rdflib.RDFS.Class) not in vocab_graph:
        print("⚠️ Attention : La classe Ability n'existe pas dans le vocabulaire !")
        return None

    if (hidden_ability_class, rdflib.RDF.type, rdflib.RDFS.Class) not in vocab_graph:
        print("⚠️ Attention : La classe HiddenAbility n'existe pas dans le vocabulaire !")
        return None

    for ability_name, ability_url in abilities:
        entity = rdflib.URIRef(EX + re.sub(r'[^a-zA-Z0-9_]', '_', ability_name))

        # Définir l'Ability comme appartenant à la classe Ability
        new_graph.add((entity, rdflib.RDF.type, ability_class))
        new_graph.add((entity, rdflib.RDFS.label, rdflib.Literal(ability_name)))

        # Vérifier si c'est une Hidden Ability et l'ajouter correctement
        if ability_name in hidden_abilities:
            new_graph.add((entity, rdflib.RDF.type, hidden_ability_class))
            print(f"🟢 Hidden Ability ajoutée : {ability_name}")
        
        # Récupérer les détails de l'ability
        ability_details = fetch_ability_details(ability_url)
        if ability_details:
            # Ajouter les effets par génération
            for key, value in ability_details.items():
                if key.startswith("Generation"):
                    # Ajouter l'effet pour cette génération
                    new_graph.add((entity, SCHEMA[key], rdflib.Literal(value)))
                else:
                    # Ajouter d'autres propriétés (comme "Effect", "Pokémon with this ability", etc.)
                    new_graph.add((entity, SCHEMA[key], rdflib.Literal(value)))

    return new_graph

# Exécution principale
vocab_graph = load_vocabulary()
all_abilities = fetch_all_abilities()
hidden_abilities = fetch_hidden_abilities()

if all_abilities:
    rdf_graph = create_rdf_graph_for_abilities(all_abilities, hidden_abilities, vocab_graph)

    if rdf_graph:
        # Sauvegarde uniquement des abilities dans "pokemonAbilities.ttl"
        ttl_file_path = "pokemonAbilities.ttl"

        try:
            rdf_graph.serialize(destination=ttl_file_path, format="turtle", encoding="utf-8")
            print(f"✅ Fichier Turtle mis à jour avec uniquement les abilities Pokémon : {ttl_file_path}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde du fichier Turtle : {e}")
