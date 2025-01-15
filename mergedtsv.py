import csv
import rdflib
from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS
import unidecode  # Pour retirer les accents et normaliser
import re

# Définition des namespaces
EX = Namespace("http://example.org/pokemon/")
DBP = Namespace("http://dbpedia.org/property/")
SCHEMA = Namespace("http://schema.org/")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

# Charger le graphe RDF principal
g = rdflib.Graph()
try:
    g.parse("merged_pokemon_knowledge_graph.ttl", format="turtle")
    print("✅ Fichier RDF principal chargé avec succès.")
except Exception as e:
    print(f"❌ Erreur lors du chargement du fichier RDF principal : {e}")

# Normaliser un nom pour le comparer de manière fiable
def normalize_name(name):
    name = re.sub(r'\s*\(.*?\)', '', name)
    return unidecode.unidecode(name.lower().strip())

# Charger les données multilingues depuis le fichier TSV
def load_multilingual_data(tsv_file):
    multilingual_data = {}
    with open(tsv_file, encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            entity_type = row['type'].strip()
            entity_id = row['id'].strip().zfill(4)  # Uniformisation avec 4 chiffres
            label = row['label'].strip()
            language = row['language'].strip().lower()
            
            # Conversion des balises de langue
            lang_map = {
                "english": "en", "french": "fr", "german": "de",
                "italian": "it", "spanish": "es", "japanese": "ja",
                "korean": "ko", "chinese": "zh", "czech": "cs"
            }
            language = lang_map.get(language, None)
            if language is None:
                print(f"⚠️ Langue inconnue ignorée : {row['language']}")
                continue

            # Stockage basé sur ID + Type
            key = (entity_type.lower(), entity_id)
            if key not in multilingual_data:
                multilingual_data[key] = set()  # Utilisation de set() pour éviter les doublons
            multilingual_data[key].add((label, language))
    return multilingual_data

# Fusionner les données multilingues avec le graphe RDF
def merge_rdf_with_multilingual_data(multilingual_data):
    entities_updated = 0
    entities_not_found = 0

    for subject, _, ndex in g.triples((None, EX.ndex, None)):
        ndex_value = ndex.value.strip().zfill(4)
        key = ('pokemon', ndex_value)

        # Vérifier si le Pokémon est bien dans le dictionnaire multilingue
        if key in multilingual_data:
            existing_labels = set(g.objects(subject, SCHEMA.name))  # Récupérer les labels existants

            for label, lang in multilingual_data[key]:
                literal = Literal(label, lang=lang)
                if literal not in existing_labels:  # Ajouter uniquement s'il n'existe pas
                    g.add((subject, SCHEMA.name, literal))
            print(f"✅ Fusion réussie pour : {subject} (ndex : {ndex_value})")
            entities_updated += 1
        else:
            entities_not_found += 1
            print(f"⚠️ Aucune correspondance trouvée pour : {subject} (ndex : {ndex_value})")

    print(f"\n✅ Fusion terminée : {entities_updated} entités mises à jour, {entities_not_found} non trouvées.")

# Sauvegarder le graphe fusionné
def save_graph_to_file(output_file):
    g.serialize(destination=output_file, format="turtle")
    print(f"\n✅ Fichier RDF fusionné sauvegardé sous : {output_file}")

# Fonction principale
def main():
    tsv_file = "pokedex-i18n.tsv"
    try:
        multilingual_data = load_multilingual_data(tsv_file)
        merge_rdf_with_multilingual_data(multilingual_data)
        save_graph_to_file("tsv_merged_output.ttl")
    except Exception as e:
        print(f"❌ Erreur pendant le processus : {e}")

if __name__ == "__main__":
    main()
