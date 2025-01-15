from rdflib import Graph, Namespace, RDF, XSD
import os

# Définir les namespaces
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
DBO = Namespace("http://dbpedia.org/ontology/")
DBP = Namespace("http://dbpedia.org/property/")
DBR = Namespace("http://dbpedia.org/resource/")
EX = Namespace("http://example.org/pokemon/")

# Chemin du répertoire contenant les fichiers .ttl
directory = "./data"

# Créer un graphe RDF vide
merged_graph = Graph()

# Charger le vocabulaire RDF (si vous avez un fichier séparé pour le vocabulaire)
vocab_file = "vocabulary_demo.ttl"
if os.path.exists(vocab_file):
    try:
        merged_graph.parse(vocab_file, format="turtle")
        print(f"Vocabulaire chargé depuis : {vocab_file}")
    except Exception as e:
        print(f"Erreur lors du chargement du vocabulaire {vocab_file} : {e}")
else:
    print(f"Le fichier de vocabulaire {vocab_file} n'existe pas. Ignorer le chargement du vocabulaire.")

# Parcourir tous les fichiers dans le répertoire
for filename in os.listdir(directory):
    if filename.endswith(".ttl") and filename != vocab_file:  # Éviter de charger le vocabulaire deux fois
        file_path = os.path.join(directory, filename)
        print(f"Traitement du fichier : {file_path}")
        
        try:
            # Charger le fichier .ttl dans un graphe temporaire
            temp_graph = Graph()
            temp_graph.parse(file_path, format="turtle")
            
            # Ajouter les triplets du graphe temporaire au graphe fusionné
            merged_graph += temp_graph
            print(f"Fichier {filename} fusionné avec succès.")
        except Exception as e:
            print(f"Erreur lors du traitement du fichier {filename} : {e}")

# Fonction pour lier les entités
def link_entities(graph, property_uri, domain_class, range_class):
    """
    Lie les entités en fonction d'une propriété donnée.
    :param graph: Le graphe RDF.
    :param property_uri: La propriété à lier (ex: ex:hasMove).
    :param domain_class: La classe du domaine (ex: ex:Pokemon).
    :param range_class: La classe du range (ex: ex:Move).
    """
    if (None, property_uri, None) in graph:
        for subject, _, obj in graph.triples((None, property_uri, None)):
            # Vérifier que le sujet et l'objet sont bien des instances des classes attendues
            if (subject, RDF.type, domain_class) in graph and (obj, RDF.type, range_class) in graph:
                graph.add((subject, property_uri, obj))
        print(f"Relations {property_uri} ajoutées avec succès.")
    else:
        print(f"Aucune relation {property_uri} trouvée dans le graphe fusionné.")

# Lier les entités en fonction des propriétés définies dans le vocabulaire
link_entities(merged_graph, EX.hasType, EX.Pokemon, EX.PokemonType)
link_entities(merged_graph, EX.hasAbility, EX.Pokemon, EX.Ability)
link_entities(merged_graph, EX.hasHiddenAbility, EX.Pokemon, EX.HiddenAbility)
link_entities(merged_graph, EX.hasEggGroup, EX.Pokemon, EX.EggGroup)
link_entities(merged_graph, EX.hasMove, EX.Pokemon, EX.Move)
link_entities(merged_graph, EX.hasPower, EX.Move, XSD.integer)
link_entities(merged_graph, EX.hasAccuracy, EX.Move, XSD.string)
link_entities(merged_graph, EX.hasCategory, EX.Move, XSD.string)
link_entities(merged_graph, EX.hasType, EX.Move, EX.PokemonType)
link_entities(merged_graph, EX.hasEpisode, EX.Episode, XSD.string)
link_entities(merged_graph, EX.hasGeneration, EX.Pokemon, XSD.integer)
link_entities(merged_graph, EX.hasImage, EX.Pokemon, XSD.anyURI)
link_entities(merged_graph, EX.relatedToDbpedia, EX.Pokemon, DBR.Pokemon)

# Sauvegarder le graphe fusionné dans un nouveau fichier .ttl
output_file = "merged_output.ttl"
try:
    merged_graph.serialize(destination=output_file, format="turtle")
    print(f"Fichier fusionné sauvegardé sous : {output_file}")
except Exception as e:
    print(f"Erreur lors de la sauvegarde du fichier fusionné : {e}")