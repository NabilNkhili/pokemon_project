import requests
import rdflib
import re
from bs4 import BeautifulSoup

# Définition des namespaces RDF
EX = rdflib.Namespace("http://example.org/pokemon/")
SCHEMA = rdflib.Namespace("http://schema.org/")
XSD = rdflib.Namespace("http://www.w3.org/2001/XMLSchema#")

# 📌 URL des Moves (Mouvements Pokémon)

def fetch_moves_list():
    url = 'https://bulbapedia.bulbagarden.net/wiki/List_of_moves'
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Erreur lors de la récupération des données : {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    moves_table = soup.find('table', {'class': 'sortable'})
    
    if not moves_table:
        print("Table des mouvements introuvable sur la page.")
        return []

    moves = []
    for row in moves_table.find_all('tr')[1:]:  # Ignorer l'en-tête
        cols = row.find_all('td')
        if len(cols) > 1:
            move_name = cols[1].get_text(strip=True)
            move_type = cols[2].get_text(strip=True)
            move_category = cols[3].get_text(strip=True)
            move_pp = cols[4].get_text(strip=True)
            move_power = cols[5].get_text(strip=True)
            move_accuracy = cols[6].get_text(strip=True)
            
            move_url = f"https://bulbapedia.bulbagarden.net/wiki/{move_name.replace(' ', '_')}_(move)"

            moves.append({
                'name': move_name,
                'type': move_type,
                'category': move_category,
                'pp': move_pp,
                'power': move_power,
                'accuracy': move_accuracy,
                'url': move_url

            })
    return moves

# 📌 Récupération de l'image en haute résolution
def fetch_move_image(move_url):
    response = requests.get(move_url)
    if response.status_code != 200:
        print(f"❌ Impossible d'accéder à {move_url}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Recherche du lien de l'image principale
    image_link_tag = soup.find('a', {'href': re.compile(r'File:.*\.(png|jpg)')})
    if image_link_tag:
        image_page_url = "https://bulbapedia.bulbagarden.net" + image_link_tag['href']

        # Aller sur la page de l’image pour récupérer son URL finale
        response_image_page = requests.get(image_page_url)
        if response_image_page.status_code != 200:
            print(f"❌ Impossible d'accéder à la page image {image_page_url}")
            return None

        soup_image_page = BeautifulSoup(response_image_page.text, 'html.parser')
        image_tag = soup_image_page.find('img')

        if image_tag and 'src' in image_tag.attrs:
            image_url = image_tag['src']

            # Convertir en URL haute résolution
            if "/thumb/" in image_url:
                image_url = re.sub(r'/thumb/', '/', image_url)
                image_url = re.sub(r'/\d+px-.*', '', image_url)

            if image_url.startswith("//"):
                image_url = "https:" + image_url
            
            return image_url

    print(f"⚠️ Aucune image trouvée pour {move_url}")
    return None

def create_moves_rdf(moves):
    """Crée un graphe RDF structuré avec des valeurs bien typées."""
    g = rdflib.Graph()
    g.bind('ex', EX)
    g.bind('schema1', SCHEMA)
    g.bind('xsd', XSD)

    # 📌 Déclaration de la classe Move
    g.add((EX.Move, rdflib.RDF.type, rdflib.RDFS.Class))

    # 📌 Déclaration de la propriété ex:hasType
    g.add((EX.hasType, rdflib.RDF.type, rdflib.RDF.Property))
    g.add((EX.hasType, rdflib.RDFS.domain, EX.Move))  # Le domaine est Move
    g.add((EX.hasType, rdflib.RDFS.range, EX.PokemonType))  # Le range est PokemonType
    g.add((EX.hasType, rdflib.RDFS.label, rdflib.Literal("hasType")))
    g.add((EX.hasType, rdflib.RDFS.comment, rdflib.Literal("Indique le type d'un Move (ex: Feu, Eau, Plante, etc.).")))

    for move in moves:
        move_uri = rdflib.URIRef(EX + re.sub(r'[^a-zA-Z0-9_]', '_', move['name'].replace(' ', '_')))
        g.add((move_uri, rdflib.RDF.type, EX.Move))
        g.add((move_uri, rdflib.RDFS.label, rdflib.Literal(move['name'])))

        # 🟡 **Ajout du Type avec ex:hasType**
        move_type_uri = rdflib.URIRef(EX + re.sub(r'[^a-zA-Z0-9_]', '_', move['type'].replace(' ', '_')))
        g.add((move_uri, EX.hasType, move_type_uri))  # Utilisation de ex:hasType

        # 🟡 **Ajout des propriétés avec le bon type**
        if move['accuracy'].replace('%', '').isdigit():
            g.add((move_uri, SCHEMA.accuracy, rdflib.Literal(int(move['accuracy'].replace('%', '')), datatype=XSD.integer)))
        else:
            g.add((move_uri, SCHEMA.accuracy, rdflib.Literal("unlimited", datatype=XSD.string)))  # Cas des attaques à précision infinie

        if move['power'].isdigit():
            g.add((move_uri, SCHEMA.power, rdflib.Literal(int(move['power']), datatype=XSD.integer)))

        if move['pp'].isdigit():
            g.add((move_uri, SCHEMA.pp, rdflib.Literal(int(move['pp']), datatype=XSD.integer)))

        # **On garde `Category` et `Generation` sans les changer**
        g.add((move_uri, SCHEMA.category, rdflib.Literal(move['category'])))

        print(f"✅ Move ajouté : {move['name']}")
        
        # 📌 Ajout de l'image
        image_url = fetch_move_image(move['url'])
        if image_url:
            g.add((move_uri, SCHEMA.image, rdflib.Literal(image_url)))

        print(f"✅ Move ajouté : {move['name']} | Image : {image_url if image_url else '🚫 Pas d’image'}")

    return g


def main():
    moves = fetch_moves_list()
    if not moves:
        print("Aucun mouvement récupéré.")
        return

    rdf_graph = create_moves_rdf(moves)
    rdf_graph.serialize(destination="pokemon_moves.ttl", format="turtle", encoding="utf-8")
    print(f"Fichier RDF généré avec succès : pokemon_moves.ttl ({len(moves)} mouvements extraits)")

if __name__ == "__main__":
    main()
