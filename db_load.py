'''
this module will import all information from the  PG RDFs passed in
the system arguments and add them to the database

Usage:
    $ python new_db_load.py files_to_load 
    or 
    $ python new_db_load.py -d directory_to_load
'''

import sys,os
from gute import db,Agent,Text,Work,Alias,LCSH
from gute_rdf import PGGraph,NoTitleError
from sqlalchemy.exc import IntegrityError

limit = 100 #number of works to commit to database at once

def parse_agent_info(agent_id,agent_info):
    A = Agent(id=agent_id,**{key:value for key,value in agent_info.items() if key != 'aliases'})
    if 'aliases' in agent_info:
        for other_name in agent_info['aliases']:
            if other_name:
                A.aliases.append(db.session.merge(Alias(name=other_name)))
    return db.session.merge(A) 

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        return instance

def load_into_db(works):
    refs = set()
    for work in works:
        db.session.add(work)
        assert isinstance(work.title,unicode)
        refs.add(work.title)
    try:
        db.session.commit()
        print u'Added the following texts (all told, {0} of them) to the DB: {1}'.format(len(refs),','.join(refs))
    except IntegrityError:
        db.session.rollback()
        print u'Some of The following texts were already loaded into the database: {0}'.format(',\n\r'.join(refs))

work_one_to_one_properties = {
    'title',
    'publication_date',
    'call_number'
   }
agents = {}
lcshs = {}
paths = sys.argv[1:] if  sys.argv[1] != '-d' else [sys.argv[2]+f for f in os.listdir(sys.argv[2])]
filenames = [f for f in paths if f[-4:] == '.rdf']

already_loaded = set(work.id for work in Work.query.all())

this_batch = []
for i,filename in enumerate(filenames):
    print u'Loading {0}. {1!r} ...'.format(i,filename) 
    pg = PGGraph()
    pg.parse(filename)
    try:
        info = pg.get_work_info()
    except NoTitleError:
        print u'No title found for {0!s}. Continuing without loading it into DB.'.format(filename)
        continue
    if pg.get_work_id() in already_loaded:
        print u'{0!s} has already been loaded. Skipping it...'.format(filename)
        continue

    W = Work(id=pg.get_work_id(),title=info['title'])
    if 'lcc' in info:
        W.call_number = ''.join(info['lcc'])
    if 'lcsh' in info:
        for lcsh in info['lcsh']:
            lcsh = lcsh.lower()
            if lcsh not in lcshs:
                lcshs[lcsh]= db.session.merge(LCSH(subject_heading=lcsh))
            W.LCSH.append(lcshs[lcsh])
    for text_url in info['texts']:
        W.texts.append(Text(url=text_url))
    for agent_id,agent_info in info['agents'].items():
        if agent_id not in agents:
            agents[agent_id] = parse_agent_info(agent_id,agent_info)
        W.agents.append(agents[agent_id])
    try: #supa hacky, like this entire script
        W.title.decode('utf-8').encode('ascii')
    except UnicodeDecodeError:
        print u'Non-english characters: {0}. Skipping...'.format(W.title)
    this_batch.append(W)
    if len(this_batch) == limit:
        load_into_db(this_batch)
        this_batch = []
if this_batch:
    load_into_db(this_batch)

