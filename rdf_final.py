import requests
import time
from rdflib import Graph, Literal, URIRef, Namespace, DC
from rdflib.namespace import RDF, RDFS, FOAF
import logging
from tqdm import tqdm
import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PokemonEnricher:
    def __init__(self):
        self.EX = Namespace("http://example.org/pokemon/")
        self.EX1 = Namespace("http://example.org/pokemon/episodes/")
        self.schema = Namespace("http://schema.org/")
        self.base_api_url = "https://bulbapedia.bulbagarden.net/w/api.php"
        self.headers = {'User-Agent': 'PokemonRDFEnricher/1.0'}

        self.categories = {
            "pokemon": self.EX.Pokemon,
            "move": self.EX.Move,
            "item": self.EX.Item,
            "ability": self.EX.Ability,
            "episode": self.EX1.Episode,
            "game": self.EX.Game,
            "character": self.EX.Character
        }

    def get_page_metadata(self, page_title):
        """Récupère les métadonnées depuis Bulbapedia."""
        params = {
            "action": "parse",
            "page": page_title,
            "prop": "templates|images|links|externallinks",
            "format": "json"
        }
        time.sleep(0.1)
        try:
            response = requests.get(self.base_api_url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erreur API pour {page_title}: {e}")
            return None

    def clean_image_name(self, image_name):
        """Formater correctement l'URL de l'image."""
        return f"https://bulbapedia.bulbagarden.net/wiki/File:{image_name.replace(' ', '_')}"

    def process_images(self, g, entity_uri, images):
        """Ajoute les images trouvées dans le RDF."""
        for image in images:
            if isinstance(image, str) and any(ext in image.lower() for ext in ['.png', '.jpg']):
                image_uri = self.clean_image_name(image)
                g.add((URIRef(entity_uri), self.schema.image, URIRef(image_uri)))
                g.add((URIRef(entity_uri), FOAF.depiction, URIRef(image_uri)))
                logging.info(f"Image ajoutée pour {entity_uri} : {image_uri}")

    def process_links(self, g, entity_uri, links):
        """Ajoute les liens RDF pour les entités associées."""
        for link in links:
            if isinstance(link, dict) and 'ns' in link and link['ns'] == 0:
                link_uri = self.EX[link['*'].replace(' ', '_')]
                g.add((URIRef(entity_uri), self.EX.relatedTo, URIRef(link_uri)))
                logging.info(f"Lien ajouté pour {entity_uri} : {link_uri}")

    def enrich_entity_data(self, g, entity_uri, metadata):
        """Enrichit l'entité RDF avec les données de Bulbapedia."""
        if not metadata or 'parse' not in metadata:
            logging.warning(f"Aucune métadonnée trouvée pour {entity_uri}")
            return False
        
        parse_data = metadata['parse']
        logging.info(f"Métadonnées récupérées pour {entity_uri} : {parse_data.keys()}")

        if 'images' in parse_data:
            self.process_images(g, entity_uri, parse_data['images'])
        if 'links' in parse_data:
            self.process_links(g, entity_uri, parse_data['links'])
        
        return True

    def enrich_rdf(self, input_file, output_file):
        """Charge ton RDF existant et enrichit toutes les entités."""
        start_time = datetime.datetime.now()
        print(f"\nDébut de l'enrichissement : {start_time.strftime('%H:%M:%S')}")

        # Charger le graphe RDF existant
        g = Graph()
        g.parse(input_file, format="turtle")

        total_processed = 0
        total_entities = 0

        # Parcourir toutes les catégories et entités
        for category, entity_type in self.categories.items():
            entities = list(g.subjects(RDF.type, entity_type))
            total_entities += len(entities)
            print(f"\nTraitement de la catégorie {category} ({len(entities)} entités)")

            # Barre de progression
            with tqdm(total=len(entities), desc=f"{category}") as pbar:
                for entity in entities:
                    label = g.value(entity, RDFS.label)
                    if label:
                        logging.info(f"Traitement de l'entité : {entity} (label: {label})")
                        try:
                            metadata = self.get_page_metadata(label)
                            if metadata and self.enrich_entity_data(g, entity, metadata):
                                total_processed += 1
                        except Exception as e:
                            logging.error(f"Erreur pour {label}: {e}")
                    else:
                        logging.warning(f"Aucun label trouvé pour l'entité : {entity}")
                    pbar.update(1)

        # Sauvegarde du graphe RDF enrichi
        end_time = datetime.datetime.now()
        duration = end_time - start_time
        print(f"\nDurée d'exécution : {duration}")
        print(f"Entités traitées avec succès : {total_processed}/{total_entities}")

        # Sauvegarde du nouveau fichier enrichi
        g.serialize(destination=output_file, format="turtle")
        print(f"✅ RDF enrichi sauvegardé dans : {output_file}")

# ✅ **Exécution principale :**
def main():
    enricher = PokemonEnricher()
    input_file = "merged_output_with_external_links.ttl"  # Ton RDF général
    output_file = "enriched_pokemon_knowledge_graphtest.ttl"
    enricher.enrich_rdf(input_file, output_file)

if __name__ == "__main__":
    main()