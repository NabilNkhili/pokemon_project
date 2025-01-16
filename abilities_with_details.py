import requests
import rdflib
import re
from bs4 import BeautifulSoup

# URLs Bulbapedia
BASE_URL = "https://bulbapedia.bulbagarden.net"
ABILITIES_URL = BASE_URL + "/wiki/Category:Abilities"

def fetch_all_abilities():
    abilities = []
    next_page_url = ABILITIES_URL

    while next_page_url:
        response = requests.get(next_page_url)
        if response.status_code != 200:
            print(f"Erreur API : {response.status_code}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        abilities_links = soup.select('div.mw-category-group ul li a')

        for a in abilities_links:
            ability_name = a.text.strip()
            if "(Ability)" in ability_name:
                ability_name = ability_name.replace(" (Ability)", "")
                ability_url = BASE_URL + a['href']
                abilities.append((ability_name, ability_url))

        # Passer à la page suivante
        next_page_link = soup.find('a', string="next page")
        next_page_url = BASE_URL + next_page_link['href'] if next_page_link else None

    print(f"{len(abilities)} Abilities trouvées.")
    return abilities

def fetch_ability_details(ability_url):
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
            
            # Séparation plus propre par génération
            if "Generation" in key:
                matches = re.findall(r'(Generation \w+)(.*?)(?=Generation|\Z)', value)
                for generation, description in matches:
                    generation_key = generation.replace(' ', '_')
                    infobox_data[generation_key] = description.strip()
            else:
                infobox_data[key] = value.strip()

    return infobox_data

def create_rdf_graph_for_abilities(abilities):
    SCHEMA = rdflib.Namespace("http://schema.org/")
    EX = rdflib.Namespace("http://example.org/pokemon/")
    g = rdflib.Graph()
    g.bind('schema1', SCHEMA, override=True)
    g.bind('ex', EX, override=True)

    for ability_name, ability_url in abilities:
        entity = rdflib.URIRef(EX + re.sub(r'[^a-zA-Z0-9_]', '_', ability_name))
        g.add((entity, rdflib.RDF.type, EX.Ability))
        g.add((entity, rdflib.RDFS.label, rdflib.Literal(ability_name)))

        infobox_data = fetch_ability_details(ability_url)
        for key, value in infobox_data.items():
            clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key).replace(' ', '_')
            predicate = SCHEMA[clean_key]

            # Ajout uniquement si la valeur est non vide
            if value.strip():
                g.add((entity, predicate, rdflib.Literal(value)))
            else:
                print(f" Clé détectée mais vide : {key}")

        print(f" Ability ajoutée : {ability_name}")

    return g

# Exécution principale
all_abilities = fetch_all_abilities()  # Récupère toutes les capacités
rdf_graph = create_rdf_graph_for_abilities(all_abilities)

# Sauvegarde dans un fichier Turtle
ttl_file_path = "abilities_all.ttl"
rdf_graph.serialize(destination=ttl_file_path, format="turtle", encoding="utf-8")
print(f" Fichier RDF généré avec succès : {ttl_file_path}")