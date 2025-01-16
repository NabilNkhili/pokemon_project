from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDFS, DCTERMS

g1 = Graph()
g1.parse("bulbapedia_all_pages.ttl", format="turtle")

g2 = Graph()
g2.parse("tsv_merged_output.ttl", format="turtle")

dbo = Namespace("http://dbpedia.org/ontology/")
wd = Namespace("https://www.wikidata.org/wiki/")
dbp = Namespace("http://dbpedia.org/resource/")
ex = Namespace("http://example.org/pokemon/")
page = Namespace("http://example.org/bulbapedia/page/")

# Fonction pour extraire le nom de la ressource à partir d'une URI
def extract_resource_name(uri):
    # Extraire le dernier segment de l'URI
    name = uri.split("/")[-1]
    name = name.split("(")[0].strip()
    name = name.replace("_", " ").strip()
    return name

# Dictionnaire pour stocker les correspondances entre les noms et les URIs de g1
resource_to_uri = {}

for s, p, o in g1:
    if p == dbo.wikiPageExternalLink:
        resource_name = extract_resource_name(str(s))
        resource_to_uri[resource_name.lower()] = (s, o)  # Stocker l'URI et le lien externe

for s2 in g2.subjects(RDFS.label, None):
    resource_name_g2 = extract_resource_name(str(s2))
    
    if resource_name_g2.lower() in resource_to_uri:
        s1, external_link = resource_to_uri[resource_name_g2.lower()]
        
        g2.add((s2, dbo.wikiPageExternalLink, external_link))
        
        dbpedia_link = URIRef(f"http://dbpedia.org/resource/{resource_name_g2.replace(' ', '_')}")
        g2.add((s2, dbo.wikiPageExternalLink, dbpedia_link))
        
        wikidata_link = URIRef(f"https://www.wikidata.org/wiki/{resource_name_g2.replace(' ', '_')}")
        g2.add((s2, dbo.wikiPageExternalLink, wikidata_link))

g2.serialize(destination="KG.ttl", format="turtle")
print("Fusion terminée. Résultat sauvegardé dans 'KG.ttl'.")