import nltk,collections,requests
from BeautifulSoup import BeautifulSoup

'''
Central location for nlp work
'''

def tokenize_work(corpus):
    sentences = nltk.sent_tokenize(corpus)
    sentences = [nltk.word_tokenize(sent) for sent in sentences]
    return [nltk.pos_tag(sent) for sent in sentences]

def named_entities(sentences):
    chunked = [nltk.ne_chunk(sent) for sent in sentences]
    nes = []
    for tree in chunked:
        for subtree in tree.subtrees():
            if subtree.node != 'S':
                nes.append(subtree)
    return nes

def make_ne_freq_dist(nes):
    d = collections.defaultdict(lambda : collections.defaultdict(int))
    for ne in nes:
        d[ne.node][' '.join(p[0] for p in ne.leaves())] += 1
    r = {}
    for ne_type in d:
        r[ne_type] = sorted(d[ne_type].items(),key=lambda x:x[1],reverse=True)
    for n in  r['PERSON']: print n
    return r

def get_links_to_dbpedia(names):
    """Takes a list of names and searches for links to their dbpedia page"""
    links = []
    for name in names:
        payload = {'QueryClass': 'person', 'QueryString': name}
        r = requests.get('http://lookup.dbpedia.org/api/search.asmx/KeywordSearch', params=payload)
        soup = BeautifulSoup(r.content)
        if soup.arrayofresult.result != None:
            if soup.arrayofresult.result.uri != None:
                print name, soup.arrayofresult.result.uri.text
                links.append(name, soup.arrayofresult.result.uri.text)
    return links

def straight_from_dbpedia(names):
    """Takes a list of names and gets whatever dbpedia page appears for that name"""
    for name in names:
        name = name.replace (" ", "_")
        r = requests.get('http://dbpedia.org/data/' + name + '.json')
        the_stuff = r.json()
        for key in the_stuff: print key

def dbpedia_spotlight_parse():
    """Sends a text off to be parsed by DBpedia Spotlight"""
    text = "President Obama called Wednesday on Congress to extend a tax break for students included in last year's economic stimulus package, arguing that the policy provides more generous assistance."
    url = 'http://spotlight.dbpedia.org/rest/annotate'
    sparql = """
            SELECT * WHERE {
            ?p a
            <http://dbpedia.org/ontology/Person> .
            ?p <dbpedia-owl:birthYear> ?birthYear.
            ?p <http://dbpedia.org/ontology/influenced> ?influenced.
            ?influenced a <http://dbpedia.org/ontology/Person>.}
            """
    payload = {'text' : text, 'confidence' : '0.2', 'support' : '20', 'sparql' : sparql}
    r = requests.get(url, params=payload)
    print r.content