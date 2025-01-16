import rdflib
import os
from flask import Flask, render_template, request
from rdflib.plugins.sparql import prepareQuery

app = Flask(__name__)

ttl_files = [
    "all_pokemon.ttl",          
    "pokemonAbilities.ttl",      
    "pokemonTypes.ttl",          
    "pokemon_moves.ttl",         
    "pokemon_all_episodes.ttl",  
    "egg_groups.ttl"     
]

g = rdflib.Graph()
for ttl_file in ttl_files:
    file_path = os.path.abspath(ttl_file)
    try:
        g.parse(file_path, format="turtle")
        print(f" Fichier {ttl_file} chargé avec succès. Nombre de triplets : {len(g)}")
    except Exception as e:
        print(f" Erreur lors du chargement de {ttl_file} : {e}")

print(f" Graph RDF chargé avec succès. Nombre total de triplets : {len(g)}")

@app.route("/")
def home():
    """Page principale"""
    return render_template("index.html")

@app.route("/sparql", methods=["GET", "POST"])
def sparql_interface():
    """Interface SPARQL pour tester les requêtes."""
    results = None
    error = None
    query_text = "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"

    if request.method == "POST":
        query_text = request.form.get("query")
        try:
            query = prepareQuery(query_text)
            results = g.query(query)
        except Exception as e:
            error = f"Erreur : {e}"

    return render_template("sparql.html", results=results, error=error, query_text=query_text)

if __name__ == "__main__":
    app.run(debug=True)
