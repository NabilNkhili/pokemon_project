import requests
import rdflib
import re
from bs4 import BeautifulSoup

BASE_URL = "https://bulbapedia.bulbagarden.net"
ITEMS_URL = BASE_URL + "/wiki/Category:Items"
ARCHIVE_BASE_URL = "https://archives.bulbagarden.net"

def fetch_all_items():
    items = []
    next_page_url = ITEMS_URL

    while next_page_url:
        response = requests.get(next_page_url)
        if response.status_code != 200:
            print(f"Erreur API : {response.status_code}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        items_links = soup.select('div.mw-category-group ul li a')

        for a in items_links:
            item_name = a.text.strip()
            if not a['href'].startswith("/wiki/Category"):
                item_url = BASE_URL + a['href']
                items.append((item_name, item_url))

        # Trouver le lien vers la page suivante
        next_page_link = soup.find('a', string="next page")
        next_page_url = BASE_URL + next_page_link['href'] if next_page_link else None

    print(f" {len(items)} Items trouvés.")
    return items

def fetch_item_details(item_url):
    """Extrait les détails et l'image correcte d'un item depuis son infobox."""
    response = requests.get(item_url)
    if response.status_code != 200:
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    infobox_data = {}
    infobox_table = soup.find('table', {'class': 'roundy'})

    if not infobox_table:
        return {}

    # Récupération de l'image avec un lien direct vers l'archive
    image_element = infobox_table.find('img')
    if image_element and 'src' in image_element.attrs:
        image_src = image_element['src']
        # Construction de l'URL complète de l'image
        if image_src.startswith(('http://', 'https://')):
            image_url = image_src  
        elif image_src.startswith("/media"):
            image_url = ARCHIVE_BASE_URL + image_src
        else:
            image_url = BASE_URL + image_src
        infobox_data['Image'] = image_url

    # Récupération des autres informations de l'infobox
    for row in infobox_table.find_all('tr'):
        header = row.find('th')
        value = row.find('td')

        if header and value:
            key = header.text.strip()
            value = value.text.strip().replace('\n', ' ')
            if value:
                if key == "Pocket" or key.startswith("Generation"):
                    # Séparer les informations par génération
                    matches = re.findall(r'(Generation \w+)\s+(.*?)(?=Generation|\Z)', value)
                    for generation, info in matches:
                        clean_generation = generation.replace(' ', '_')
                        infobox_data[clean_generation] = info.strip()
                elif key == "Artwork":
                    infobox_data['Artwork'] = value
                elif key == "Introduced in":
                    infobox_data['IntroducedIn'] = value
                else:
                    infobox_data[key] = value

    
    if 'Artwork' not in infobox_data:
        infobox_data['Artwork'] = "Pokemon Global Link artwork"  
    if 'IntroducedIn' not in infobox_data:
        infobox_data['IntroducedIn'] = "Generation VI"  # Valeur par défaut

    return infobox_data

def create_rdf_graph_for_items(items):
    """Crée un graphe RDF pour tous les items avec leurs données d'infobox et images."""
    SCHEMA = rdflib.Namespace("http://schema.org/")
    IT = rdflib.Namespace("http://example.org/items/")
    g = rdflib.Graph()
    g.bind('schema1', SCHEMA, override=True)
    g.bind('it', IT, override=True)

    for item_name, item_url in items:
        entity = rdflib.URIRef(IT + re.sub(r'[^a-zA-Z0-9_]', '_', item_name))
        g.add((entity, rdflib.RDF.type, IT.Item))
        g.add((entity, rdflib.RDFS.label, rdflib.Literal(item_name)))

        infobox_data = fetch_item_details(item_url)
        for key, value in infobox_data.items():
            clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key).replace(' ', '_')
            predicate = SCHEMA[clean_key]

            # Ajout des valeurs correctement séparées
            if isinstance(value, str) and value.strip():
                g.add((entity, predicate, rdflib.Literal(value)))
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    sub_predicate = SCHEMA[sub_key]
                    g.add((entity, sub_predicate, rdflib.Literal(sub_value)))

        print(f" Item ajouté : {item_name}")

    return g

# Exécution principale
all_items = fetch_all_items()  
rdf_graph = create_rdf_graph_for_items(all_items)

# Sauvegarde dans un fichier Turtle
ttl_file_path = "all_items_with_images.ttl"
rdf_graph.serialize(destination=ttl_file_path, format="turtle", encoding="utf-8")
print(f" Fichier RDF avec tous les items généré avec succès : {ttl_file_path}")