'''
The main workflow for adding a corpus to the database. 
'''
from gute import Work 
from load_text import get_corpus

def process_corpera(work):
    '''
    This is the main process -- it downloads the text, tokenizes it, and 
    loads it into the database
    '''
    return get_corpus(t.url for t in work.texts)

if __name__ == '__main__':
    import sys
    works = Work.query.filter(Work.id.in_(sys.argv[1:])).all()
    for work in works:
         print process_corpera(work)[:200]
