import nltk,collections

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
