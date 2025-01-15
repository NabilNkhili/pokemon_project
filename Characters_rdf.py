import requests
import rdflib
import re
from bs4 import BeautifulSoup

# URLs Bulbapedia pour les personnages
BASE_URL = "https://bulbapedia.bulbagarden.net"
CHARACTERS_URL = BASE_URL + "/wiki/Category:Characters"
ARCHIVE_BASE_URL = "https://archives.bulbagarden.net"

def fetch_all_characters():
    """Récupère tous les personnages de Bulbapedia."""
    characters = []
    next_page_url = CHARACTERS_URL

    while next_page_url:
        response = requests.get(next_page_url)
        if response.status_code != 200:
            print(f"Erreur API : {response.status_code}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        character_links = soup.select('div.mw-category-group ul li a')

        for a in character_links:
            character_name = a.text.strip()
            if not a['href'].startswith("/wiki/Category"):
                character_url = BASE_URL + a['href']
                characters.append((character_name, character_url))

        next_page_link = soup.find('a', string="next page")
        next_page_url = BASE_URL + next_page_link['href'] if next_page_link else None

    print(f"✅ {len(characters)} Personnages trouvés.")
    return characters

def fetch_character_details(character_url):
    """Extrait les détails et l'image correcte d'un personnage depuis son infobox."""
    response = requests.get(character_url)
    if response.status_code != 200:
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    infobox_data = {}
    infobox_table = soup.find('table', {'class': 'roundy'})

    if not infobox_table:
        return {}

    # Correction de l'extraction de l'image avec l'URL complète
    image_element = infobox_table.find('img')
    if image_element and 'src' in image_element.attrs:
        image_url = image_element['src']
        # Assurer que l'URL commence correctement
        if image_url.startswith("//"):
            image_url = "https:" + image_url
        infobox_data['Image'] = image_url

    for row in infobox_table.find_all('tr'):
        header = row.find('th')
        value = row.find('td')

        if header and value:
            key = header.text.strip()
            # Traitement des balises <br> pour séparer correctement
            for br in value.find_all('br'):
                br.replace_with('\n')
            value = value.text.strip()

            # Gestion des valeurs multiples après suppression des <br>
            if '\n' in value:
                values = [v.strip() for v in value.split('\n') if v.strip()]
                infobox_data[key] = values
            elif ',' in value:
                values = [v.strip() for v in value.split(',') if v.strip()]
                infobox_data[key] = values
            else:
                infobox_data[key] = value

    return infobox_data

def create_rdf_graph_for_characters(characters):
    """Crée un graphe RDF pour tous les personnages avec leurs données d'infobox et images."""
    SCHEMA = rdflib.Namespace("http://schema.org/")
    EX = rdflib.Namespace("http://example.org/pokemon/")
    g = rdflib.Graph()
    g.bind('schema1', SCHEMA, override=True)
    g.bind('ex', EX, override=True)

    for character_name, character_url in characters:
        entity = rdflib.URIRef(EX + re.sub(r'[^a-zA-Z0-9_]', '_', character_name))
        g.add((entity, rdflib.RDF.type, EX.Character))
        g.add((entity, rdflib.RDFS.label, rdflib.Literal(character_name)))

        infobox_data = fetch_character_details(character_url)
        for key, value in infobox_data.items():
            clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key).replace(' ', '_')
            predicate = SCHEMA[clean_key]
            if isinstance(value, list):
                for v in value:
                    g.add((entity, predicate, rdflib.Literal(v)))
            elif value.strip():
                g.add((entity, predicate, rdflib.Literal(value)))
            else:
                print(f"⚠️ Clé détectée mais vide : {key}")

        print(f"✅ Personnage ajouté : {character_name}")

    return g

# Exécution principale
all_characters = fetch_all_characters()  # Récupère tous les personnages
rdf_graph = create_rdf_graph_for_characters(all_characters)

# Sauvegarde dans un fichier Turtle
with open("characters_all_with_images.ttl", "w", encoding="utf-8") as f:
    f.write(rdf_graph.serialize(format="turtle"))

print(f"✅ Fichier RDF complet avec images généré avec succès : characters_all_with_images.ttl")
