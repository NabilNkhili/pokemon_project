import os
import requests
from rdflib import Graph, Namespace, URIRef
import logging
from rdflib.namespace import RDF, RDFS


# Configure logging
logging.basicConfig(filename='download.log', level=logging.ERROR)

# Define namespaces
EX = Namespace("http://example.org/pokemon/")

# Load the RDF graph
g = Graph()
g.parse("./data/all_pokemon.ttl", format="turtle")

# Define the static folder path
static_folder = 'static/images'

# Create the static folder if it doesn't exist
if not os.path.exists(static_folder):
    os.makedirs(static_folder)

# Function to download and save an image
def download_image(url, save_path):
    if os.path.exists(save_path):
        print(f"Image {save_path} already exists.")
        return
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Downloaded {url} to {save_path}")
        else:
            print(f"Failed to download {url}, status code: {response.status_code}")
            logging.error(f"Failed to download {url}, status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        logging.error(f"Error downloading {url}: {e}")

# Iterate over all Pokémon entities
for pokemon in g.subjects(RDF.type, EX.Pokemon):
    image_url = g.value(pokemon, EX.hasImage)
    ndex = g.value(pokemon, EX.ndex)
    if image_url and ndex and isinstance(image_url, URIRef) and str(image_url).startswith('http'):
        # Use ndex as filename
        filename = str(ndex) + ".png"
        save_path = os.path.join(static_folder, filename)
        download_image(str(image_url), save_path)