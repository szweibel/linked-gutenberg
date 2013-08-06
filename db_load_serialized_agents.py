from gute import Agent,db
from collections import defaultdict
from rdflib import Graph,URIRef
from datetime import datetime

for prop in dir(db.session):
    print(prop)

g = Graph()
g.parse("serialized_agents.nt", format="nt")

agents = defaultdict(dict)
predicates_to_skip = {URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), # skip b/c we know they're agents
    URIRef('http://www.gutenberg.org/2009/pgterms/alias'),  # skip to handle later
    URIRef('http://www.gutenberg.org/2009/pgterms/deathdate'),  # skip b/c below error
    URIRef('http://www.gutenberg.org/2009/pgterms/birthdate')}  # skip b/c below error
'''
Saving years to database is failing right now because of a limitation in the datetime.strfrtime method
that won't handle pre-1900 years
See: http://stackoverflow.com/questions/6571562/python-time-module-wont-handle-year-before-1900
'''
predicate_column_type = {
    URIRef('http://www.gutenberg.org/2009/pgterms/name'): ('name', 'text'),
    URIRef('http://www.gutenberg.org/2009/pgterms/webpage'): ('wiki_page', 'text'),
    URIRef('http://www.gutenberg.org/2009/pgterms/birthdate'): ('birth_date', 'year'),
    URIRef('http://www.gutenberg.org/2009/pgterms/deathdate'): ('death_date', 'year')
}

problems = Graph()  # to hold unencodeable

for s, p, o in g:
    if p in predicates_to_skip:  # ignore triples declaring type = agent or aliases
        continue
    try:
        agent_id =  str(s).split('/')[-1]
        column = predicate_column_type[p][0]
        agents[agent_id][column] = str(o) if predicate_column_type[p][1] == 'text' else datetime(int(o),1,1)
    except:
        problems.add((s,p,o))

for agent_id,agent_info in agents.items():
    db.session.add(Agent(id=agent_id,**agent_info))

db.session.commit()
db.session.remove()

with open('unencodeable.nt', mode='wb') as f:  # serialize fuck ups
    problems.serialize(destination=f, format='nt')
