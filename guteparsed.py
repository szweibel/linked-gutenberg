from rdflib import Graph, URIRef
from rdflib.namespace import RDF, FOAF
import pprint


g = Graph()
g.parse("serialized_agents.nt", format="nt")

for j in g.triples((None,URIRef('http://www.gutenberg.org/2009/pgterms/name'),None)):
    print(j)