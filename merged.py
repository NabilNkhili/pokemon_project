import rdflib
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS
import os

EX = Namespace("http://example.org/pokemon/")
DBP = Namespace("http://dbpedia.org/property/")
SCHEMA = Namespace("http://schema.org/")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

main_graph = Graph()

# Charger le vocabulaire RDF
try:
    main_graph.parse("data/vocabulary_demo.ttl", format="turtle")
    print(" Vocabulaire chargé avec succès.")
except Exception as e:
    print(f" Erreur lors du chargement du vocabulaire : {e}")

# Fusionner tous les fichiers RDF dans le dossier data/
data_folder = "data/"
for file in os.listdir(data_folder):
    if file.endswith(".ttl") and file != "vocabulary_demo.ttl":
        file_path = os.path.join(data_folder, file)
        try:
            main_graph.parse(file_path, format="turtle")
            print(f" Fichier chargé : {file}")
        except Exception as e:
            print(f" Erreur lors du chargement de {file} : {e}")

# Fonction pour relier automatiquement les entités entre elles
def link_entities(graph):
    for pokemon in graph.subjects(RDF.type, EX.Pokemon):
        for pokemon_type in graph.objects(pokemon, EX.hasType):
            if (pokemon_type, RDF.type, EX.PokemonType) not in graph:
                graph.add((pokemon_type, RDF.type, EX.PokemonType))
                
        for ability in graph.objects(pokemon, EX.hasAbility):
            if (ability, RDF.type, EX.Ability) not in graph:
                graph.add((ability, RDF.type, EX.Ability))
        
        for egg_group in graph.objects(pokemon, EX.hasEggGroup):
            if (egg_group, RDF.type, EX.EggGroup) not in graph:
                graph.add((egg_group, RDF.type, EX.EggGroup))

link_entities(main_graph)

# Sauvegarder le graphe fusionné
output_file = "merged_pokemon_knowledge_graph.ttl"
main_graph.serialize(destination=output_file, format="turtle")
print(f"\n Fichier RDF fusionné sauvegardé sous : {output_file}")
