import requests
import rdflib
import re
from bs4 import BeautifulSoup

# URLs Bulbapedia pour les jeux
BASE_URL = "https://bulbapedia.bulbagarden.net"
GAMES_URL = BASE_URL + "/wiki/Category:Games"

def fetch_all_games(start_from="Adventure Log"):
    """Récupère tous les jeux de Bulbapedia, en commençant à partir d'un jeu spécifique."""
    games = []
    next_page_url = GAMES_URL
    start_collecting = False

    while next_page_url:
        response = requests.get(next_page_url)
        if response.status_code != 200:
            print(f"Erreur API : {response.status_code}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        games_links = soup.select('div.mw-category-group ul li a')

        for a in games_links:
            game_name = a.text.strip()
            if "List of" in game_name or "games" in game_name.lower():
                continue

            if game_name == start_from:
                start_collecting = True

            if start_collecting and not a['href'].startswith("/wiki/Category"):
                game_url = BASE_URL + a['href']
                games.append((game_name, game_url))

        next_page_link = soup.find('a', string="next page")
        next_page_url = BASE_URL + next_page_link['href'] if next_page_link else None

    print(f"✅ {len(games)} Jeux valides trouvés.")
    return games

def fetch_game_details(game_url):
    """Extrait les détails et l'image correcte d'un jeu depuis son infobox."""
    response = requests.get(game_url)
    if response.status_code != 200:
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    infobox_data = {}
    infobox_table = soup.find('table', {'class': 'roundy'})

    if not infobox_table:
        return {}

    # Extraction de l'image principale
    image_element = infobox_table.find('img')
    if image_element and 'src' in image_element.attrs:
        image_url = image_element['src']
        if image_url.startswith("//"):
            image_url = "https:" + image_url
        infobox_data['Image'] = image_url
    else:
        infobox_data['Image'] = "Unknown"

    for row in infobox_table.find_all('tr'):
        header = row.find('th')
        value = row.find('td')

        if header and value:
            key = header.text.strip().replace(':', '')
            for br in value.find_all('br'):
                br.replace_with('\n')
            value = value.text.strip()
            value = re.sub(r'\[\d+\]', '', value)

            if '\n' in value:
                values = [v.strip() for v in value.split('\n') if v.strip()]
                infobox_data[key] = values if values else "Unknown"
            elif ',' in value:
                values = [v.strip() for v in value.split(',') if v.strip()]
                infobox_data[key] = values if values else "Unknown"
            else:
                infobox_data[key] = value if value else "Unknown"

    important_keys = ['Category', 'Platform', 'Players', 'Developer', 'Publisher']
    for key in important_keys:
        if key not in infobox_data:
            infobox_data[key] = "Unknown"

    return infobox_data

# Exécution principale
all_games = fetch_all_games(start_from="Adventure Log")

# Définir les namespaces
SCHEMA = rdflib.Namespace("http://schema.org/")
EX = rdflib.Namespace("http://example.org/pokemon/")

# Sauvegarde dans un fichier Turtle sans commentaires inutiles
with open("games_with_images.ttl", "w", encoding="utf-8") as f:
    f.write("@prefix ex: <http://example.org/pokemon/> .\n")
    f.write("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n")
    f.write("@prefix schema1: <http://schema.org/> .\n\n")

    for game_name, game_url in all_games:
        entity_id = re.sub(r'[^a-zA-Z0-9_]', '_', game_name)
        entity = rdflib.URIRef(EX + entity_id)
        f.write(f"ex:{entity_id} a ex:Game ;\n")
        f.write(f"    rdfs:label \"{game_name}\" ;\n")

        infobox_data = fetch_game_details(game_url)

        # Infos générales
        basic_info_keys = ['Category', 'Platform', 'Players', 'Connectivity', 'Developer', 'Publisher', 'Part of']
        for key in basic_info_keys:
            value = infobox_data.get(key, "Unknown")
            clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key).replace(' ', '_')
            if isinstance(value, list):
                f.write(f"    schema1:{clean_key} \"{', '.join(value)}\" ;\n")
            else:
                f.write(f"    schema1:{clean_key} \"{value}\" ;\n")

        # Release Dates (Ajout explicite d'un identifiant unique)
        release_dates_keys = ['Japan', 'North America', 'Australia', 'Europe', 'South Korea', 'Hong Kong', 'Taiwan']
        for key in release_dates_keys:
            value = infobox_data.get(key, "Unknown")
            clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key).replace(' ', '_')
            if isinstance(value, list):
                f.write(f"    schema1:releaseDate_{clean_key} \"{', '.join(value)}\" ;\n")
            else:
                f.write(f"    schema1:releaseDate_{clean_key} \"{value}\" ;\n")

        # Image (Ajout explicite d'un identifiant unique)
        f.write(f"    schema1:imageURL \"{infobox_data.get('Image', 'Unknown')}\" .\n\n")

        print(f"✅ Jeu ajouté : {game_name}")

print(f"✅ Fichier RDF avec tous les jeux généré avec succès : games_with_images.ttl")
