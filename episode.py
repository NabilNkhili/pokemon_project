import requests
from bs4 import BeautifulSoup
import rdflib
import re
import time

BASE_URL = "https://bulbapedia.bulbagarden.net"
EPISODES_URL = BASE_URL + "/wiki/List_of_animated_series_episodes"

def fetch_episode_links():
    """Récupère tous les liens vers les pages d'épisodes en filtrant les balises invalides avec gestion des erreurs."""
    retries = 3  # Nombre de tentatives en cas d'échec
    episode_links = []

    for attempt in range(retries):
        try:
            response = requests.get(EPISODES_URL, timeout=10)
            if response.status_code != 200:
                print(f"❌ Erreur {response.status_code} lors du chargement de la page : {EPISODES_URL}")
                continue  # Réessaye la requête

            soup = BeautifulSoup(response.text, 'html.parser')

            # ✅ Extraction sécurisée des liens
            for link in soup.select('table a'):
                try:
                    episode_name = link.text.strip()
                    episode_url = BASE_URL + link['href']
                    # Filtrer les liens internes et les catégories
                    if not "Category:" in link['href'] and episode_name:
                        episode_links.append((episode_name, episode_url))
                except KeyError:
                    print(f"⚠️ Balise ignorée, absence de 'href' : {link}")

            if episode_links:
                print(f"✅ {len(episode_links)} épisodes trouvés.")
                return episode_links

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Erreur réseau ({attempt+1}/{retries}) pour la page des épisodes : {e}")
            time.sleep(5)  # Attente avant nouvelle tentative

    print("❌ Échec final de la récupération des épisodes.")
    return []

def fetch_episode_details(episode_url):
    """Extrait les détails de l'épisode avec gestion des erreurs et délai entre les requêtes."""
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.get(episode_url, timeout=10)
            time.sleep(0.5)  # Petite pause pour éviter le blocage IP

            if response.status_code != 200:
                print(f"❌ Erreur {response.status_code} pour {episode_url}")
                continue  # Réessaye

            soup = BeautifulSoup(response.text, 'html.parser')
            infobox_table = soup.find('table', {'class': 'roundy'})
            if not infobox_table:
                print(f"❌ Aucune infobox trouvée pour : {episode_url}")
                return {}

            episode_data = {}

            # ✅ Extraction des champs de l'infobox
            for row in infobox_table.find_all('tr'):
                header = row.find('th')
                value = row.find('td')
                if header and value:
                    key = header.get_text(strip=True).lower().replace(' ', '_')
                    value_text = value.get_text(strip=True).replace('\n', ', ')
                    episode_data[key] = value_text

            # ✅ Extraction de l'image
            image_element = infobox_table.find('img')
            if image_element and 'src' in image_element.attrs:
                image_url = image_element['src']
                if image_url.startswith("//"):
                    image_url = "https:" + image_url
                elif not image_url.startswith("http"):
                    image_url = "https://archives.bulbagarden.net" + image_url
                episode_data['image'] = image_url

            print(f"✅ Données extraites depuis : {episode_url}")
            return episode_data

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Erreur réseau ({attempt+1}/{retries}) pour {episode_url}: {e}")
            time.sleep(5)  # Attente avant nouvelle tentative

    print(f"❌ Échec final pour {episode_url}, on passe au suivant.")
    return {}

def generate_rdf_graph(episode_list):
    """Génère un fichier RDF Turtle pour tous les épisodes."""
    EX = rdflib.Namespace("http://example.org/pokemon/episodes/")
    g = rdflib.Graph()
    g.bind('ex', EX)

    total_episodes = 0

    for episode_name, episode_url in episode_list:
        print(f"🔍 Extraction des données pour : {episode_name}")
        episode_entity = rdflib.URIRef(EX + re.sub(r'[^a-zA-Z0-9_]', '_', episode_name))
        g.add((episode_entity, rdflib.RDF.type, EX.Episode))
        g.add((episode_entity, rdflib.RDFS.label, rdflib.Literal(episode_name)))

        episode_details = fetch_episode_details(episode_url)
        if episode_details:
            for key, value in episode_details.items():
                g.add((episode_entity, EX[key], rdflib.Literal(value)))
            total_episodes += 1
        else:
            print(f"⚠️ Aucune donnée ajoutée pour : {episode_name}")

        # ✅ Sauvegarde toutes les 50 entrées pour éviter la perte en cas d'arrêt
        if total_episodes % 50 == 0:
            g.serialize("pokemon_all_episodes.ttl", format="turtle", encoding="utf-8")
            print(f"💾 Sauvegarde intermédiaire après {total_episodes} épisodes.")

    # ✅ Sauvegarde finale
    g.serialize("pokemon_all_episodes.ttl", format="turtle", encoding="utf-8")
    print(f"✅ Fichier RDF généré avec succès : pokemon_all_episodes.ttl")
    print(f"🎬 Nombre total d'épisodes traités : {total_episodes}")

# ✅ Exécution principale : Récupère tous les épisodes et génère le RDF
episode_links = fetch_episode_links()
if episode_links:
    generate_rdf_graph(episode_links)
else:
    print("❌ Aucune donnée trouvée pour générer le RDF.")
