import rdflib
import os

# 📌 Liste des fichiers RDF à fusionner
ttl_files = [
    "all_pokemon.ttl",
    "pokemonAbilities.ttl",
    "pokemonTypes.ttl",
    "pokemon_moves.ttl",
    "pokemon_all_episodes.ttl",
    "egg_groups.ttl"
]

def merge_rdf_files(output_file="merged_pokemon_data.ttl"):
    """Fusionne tous les fichiers RDF en un seul fichier."""
    g = rdflib.Graph()
    
    for ttl_file in ttl_files:
        file_path = os.path.abspath(ttl_file)
        try:
            g.parse(file_path, format="turtle")
            print(f"✅ Fichier {ttl_file} chargé avec succès.")
        except Exception as e:
            print(f"❌ Erreur lors du chargement de {ttl_file} : {e}")

    g.serialize(destination=output_file, format="turtle", encoding="utf-8")
    print(f"📂 Tous les fichiers RDF ont été fusionnés dans {output_file}")

def count_rdf_triples(file="merged_pokemon_data.ttl"):
    """Compte le nombre total de triplets RDF dans un fichier Turtle."""
    g = rdflib.Graph()
    try:
        g.parse(file, format="turtle")
        total_triples = len(g)
        print(f"📊 Nombre total de triplets RDF dans {file} : {total_triples}")
        return total_triples
    except Exception as e:
        print(f"❌ Erreur lors du chargement de {file} : {e}")
        return 0

# Exécution des fonctions
merge_rdf_files()
count_rdf_triples()
