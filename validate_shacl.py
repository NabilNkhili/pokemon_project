from pyshacl import validate
import rdflib

def validate_rdf(data_file, shape_file):
    data_graph = rdflib.Graph()
    data_graph.parse(data_file, format="turtle")

    shape_graph = rdflib.Graph()
    shape_graph.parse(shape_file, format="turtle")

    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shape_graph,
        data_graph_format="turtle",
        shacl_graph_format="turtle"
    )

    if conforms:
        print(f"✅ Les données dans {data_file} sont valides.")
    else:
        print(f"❌ Erreurs détectées dans {data_file} :")
        print(results_text)

# Exemple d'utilisation :
validate_rdf("tsv_merged_output.ttl", "data/pokemon_shape.ttl")
