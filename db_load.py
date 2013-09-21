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
from gute_rdf import PGGraph
from sqlalchemy.exc import IntegrityError

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

work_one_to_one_properties = {
    'title',
    'publication_date',
    'call_number'
    }
agents = {}
lcshs = {}
paths = sys.argv[1:] if  sys.argv[1] != '-d' else [sys.argv[2]+f for f in os.listdir(sys.argv[2])]
filenames = [f for f in paths if f[-4:] == '.rdf']

for i,filename in enumerate(filenames):
    print 'Loading '+str(i)+'. '+filename+'...'
    pg = PGGraph()
    pg.parse(filename)
    info = pg.get_work_info()
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
    db.session.add(W)
    ref = info['title'] if info['title'] == str(info['title']) else filename 
    try:
         db.session.commit()
         print 'Added '+ref+' to the DB.'
    except IntegrityError:
        db.session.rollback()
        print ref+'was already loaded into the database.'




