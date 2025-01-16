import requests
from bs4 import BeautifulSoup
import rdflib

WIKI_API_URL = "https://bulbapedia.bulbagarden.net/w/api.php"
BASE_URL = "https://bulbapedia.bulbagarden.net"
EPISODES_URL = BASE_URL + "/wiki/List_of_animated_series_episodes"

CATEGORIES = ["Abilities", "Moves", "Pokémon", "Types", "Characters", "Items"]

g = rdflib.Graph()

resource_ns = rdflib.Namespace("http://example.org/bulbapedia/resource/")
page_ns = rdflib.Namespace("http://example.org/bulbapedia/page/")
dbo = rdflib.Namespace("http://dbpedia.org/ontology/")
foaf = rdflib.Namespace("http://xmlns.com/foaf/0.1/")
rdfs = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")

g.bind("resource", resource_ns)
g.bind("page", page_ns)
g.bind("dbo", dbo)
g.bind("foaf", foaf)
g.bind("rdfs", rdfs)

def get_all_pages_in_category(category):
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmlimit": "max",  
        "format": "json"
    }
    pages = []
    while True:
        response = requests.get(WIKI_API_URL, params=params)
        data = response.json()
        if "query" in data and "categorymembers" in data["query"]:
            pages.extend(data["query"]["categorymembers"])
        else:
            print(f"Aucune page trouvée pour la catégorie : {category}")
            print(f"Réponse de l'API : {data}")
            break
        if "continue" in data:
            params.update(data["continue"])
        else:
            break
    return pages

def fetch_episode_links():
    """Récupère tous les liens vers les pages d'épisodes."""
    response = requests.get(EPISODES_URL)
    if response.status_code != 200:
        print(f" Erreur lors du chargement de la page : {EPISODES_URL}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    episode_links = []

    for table in soup.find_all('table', {'class': 'roundy'}):
        for link in table.find_all('a', href=True):
            episode_name = link.text.strip()
            episode_url = BASE_URL + link['href']
            if not episode_url.endswith(('.png', '.jpg', '.jpeg', '.gif')) and "Category:" not in episode_url:
                episode_links.append((episode_name, episode_url))

    print(f" {len(episode_links)} épisodes trouvés.")
    return episode_links

def generate_rdf(pages, category=None):
    """Génère des triplets RDF pour chaque page ou épisode."""
    for page in pages:
        if isinstance(page, tuple):  
            page_title, page_url = page
            page_id = None  
        else:  
            page_title = page["title"]
            page_id = page["pageid"]
            page_url = f"https://bulbapedia.bulbagarden.net/wiki/{page_title.replace(' ', '_')}"
        
        # Création des URIs
        resource_uri = resource_ns[page_title.replace(" ", "_")]
        page_uri = page_ns[page_title.replace(" ", "_")]
        
        g.add((resource_uri, rdfs.label, rdflib.Literal(page_title)))
        g.add((resource_uri, rdflib.RDF.type, dbo.WikiEntity))
        g.add((resource_uri, dbo.wikiPage, page_uri))
        g.add((page_uri, foaf.primaryTopic, resource_uri))
        g.add((page_uri, dbo.wikiPageExternalLink, rdflib.URIRef(page_url)))

for category in CATEGORIES:
    print(f"Récupération des pages pour la catégorie : {category}")
    pages = get_all_pages_in_category(category)
    generate_rdf(pages, category)
    print(f"{len(pages)} pages récupérées pour la catégorie {category}.")

print("Récupération des épisodes...")
episode_links = fetch_episode_links()
if episode_links:
    generate_rdf(episode_links)
    print(f" {len(episode_links)} épisodes ajoutés au graphe RDF.")
else:
    print(" Aucun épisode trouvé.")

output_file = "bulbapedia_all_pages.ttl"
g.serialize(destination=output_file, format="turtle")

print(f"RDF généré avec succès. {len(g)} triplets créés.")
print(f"Fichier Turtle enregistré sous : {output_file}")