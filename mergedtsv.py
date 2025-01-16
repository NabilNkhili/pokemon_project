import csv
import rdflib
from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS
import unidecode  # Pour retirer les accents et normaliser
import re

EX = Namespace("http://example.org/pokemon/")
DBP = Namespace("http://dbpedia.org/property/")
SCHEMA = Namespace("http://schema.org/")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

g = rdflib.Graph()
try:
    g.parse("merged_pokemon_knowledge_graph.ttl", format="turtle")
    print(" Fichier RDF principal chargé avec succès.")
except Exception as e:
    print(f" Erreur lors du chargement du fichier RDF principal : {e}")

# Fonction pour mapper les langues aux balises de langue standard
def get_language_tag(lang):
    language_mapping = {
        'Japanese': 'ja',
        'Korean': 'ko',
        'Chinese': 'zh',
        'French': 'fr',
        'German': 'de',
        'Spanish': 'es',
        'Italian': 'it',
        'English': 'en',
        'official roomaji': 'ja-Latn'
    }
    return language_mapping.get(lang, 'en')

def normalize_name(name):
    # Supprimer les parenthèses et leur contenu
    name = re.sub(r'\s*\(.*?\)', '', name)
    # Supprimer les accents et autres caractères spéciaux
    name = unidecode.unidecode(name)
    # Convertir en minuscules et supprimer les espaces inutiles
    return name.lower().strip()

# Charger les données multilingues depuis le fichier TSV
def load_multilingual_data(tsv_file):
    multilingual_data = {}
    with open(tsv_file, encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            entity_type = row['type'].strip()
            entity_id = row['id'].strip().zfill(4)  
            label = row['label'].strip()
            language = row['language'].strip()

            lang_tag = get_language_tag(language)
            if lang_tag is None:
                print(f" Langue inconnue ignorée : {language}")
                continue

            key = (entity_type.lower(), entity_id)
            if key not in multilingual_data:
                multilingual_data[key] = set()  # Utilisation de set() pour éviter les doublons
            multilingual_data[key].add((label, lang_tag))
    return multilingual_data

# Fusionner les données multilingues avec le graphe RDF
def merge_rdf_with_multilingual_data(multilingual_data):
    entities_updated = 0
    entities_not_found = 0

    # Traiter les Pokémon
    for subject, _, ndex in g.triples((None, EX.ndex, None)):
        ndex_value = ndex.value.strip().zfill(4)
        key = ('pokemon', ndex_value)

        if key in multilingual_data:
            existing_labels = set(g.objects(subject, SCHEMA.name))  

            for label, lang in multilingual_data[key]:
                literal = Literal(label, lang=lang)
                if literal not in existing_labels:  
                    g.add((subject, SCHEMA.name, literal))
            print(f" Fusion réussie pour : {subject} (ndex : {ndex_value})")
            entities_updated += 1
        else:
            entities_not_found += 1
            print(f" Aucune correspondance trouvée pour : {subject} (ndex : {ndex_value})")

    for subject, _, label in g.triples((None, RDFS.label, None)):
        if (subject, RDF.type, EX.Move) in g:  
            normalized_label = normalize_name(label.value)

            for key, values in multilingual_data.items():
                if key[0] == 'move':  # On ne traite que les mouvements
                    for move_name, lang in values:
                        if normalize_name(move_name) == normalized_label:
                            # Ajouter le nom dans la langue correspondante
                            g.add((subject, SCHEMA.name, Literal(move_name, lang=lang)))
                            entities_updated += 1
                            print(f" Ajout du nom '{move_name}' ({lang}) pour : {subject}")

    for subject, _, label in g.triples((None, RDFS.label, None)):
        if (subject, RDF.type, EX.Ability) in g:  
            normalized_label = normalize_name(label.value)

            for key, values in multilingual_data.items():
                if key[0] == 'ability':  
                    for ability_name, lang in values:
                        if normalize_name(ability_name) == normalized_label:
                            # Ajouter le nom dans la langue correspondante
                            g.add((subject, SCHEMA.name, Literal(ability_name, lang=lang)))
                            entities_updated += 1
                            print(f" Ajout du nom '{ability_name}' ({lang}) pour : {subject}")

    print(f"\n Fusion terminée : {entities_updated} entités mises à jour, {entities_not_found} non trouvées.")

def save_graph_to_file(output_file):
    g.serialize(destination=output_file, format="turtle")
    print(f"\n Fichier RDF fusionné sauvegardé sous : {output_file}")

def main():
    tsv_file = "pokedex-i18n.tsv"
    try:
        multilingual_data = load_multilingual_data(tsv_file)
        merge_rdf_with_multilingual_data(multilingual_data)
        save_graph_to_file("tsv_merged_output.ttl")
    except Exception as e:
        print(f" Erreur pendant le processus : {e}")

if __name__ == "__main__":
    main()