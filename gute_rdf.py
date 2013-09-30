import os, fnmatch, datetime
import logging
from gute import Agent,db,LCSH,Work,Alias
from rdflib import Graph
from rdflib.namespace import DCTERMS,RDF,Namespace

logging.basicConfig()

PGTERMS = Namespace('http://www.gutenberg.org/2009/pgterms/')

def locate(pattern, root=os.curdir):
   '''Locate all files matching supplied filename pattern in and below
   supplied root directory.'''
   for path, dirs, files in os.walk(os.path.abspath(root)):
       for filename in fnmatch.filter(files, pattern):
           yield os.path.join(path, filename)

class IDError(ValueError):
	pass
class NoTitleError(ValueError):
        pass

class PGGraph(Graph):
	'''
	Graph for easily unpacking desired information from a Project Gutenberg RDF
	'''
	def __init__(self):
		super(PGGraph,self).__init__()
		self._agent_map = (
			('name',PGTERMS.name,True,self._safe_string),
			('birth_date',PGTERMS.birthdate,True, lambda x:datetime.datetime(int(x),1,1)),
			('death_date',PGTERMS.deathdate,True, lambda x:datetime.datetime(int(x),1,1)),
			('wiki_page',PGTERMS.webpage,True,self._safe_string),


                        ('aliases',PGTERMS.alias,False,lambda x:[self._safe_string(y)[:150] for y in x if y==str(y)])
		)
		self._work_map = (
			('title',self._get_title),
			('lcsh',self._get_lcsh),
			('lcc',self._get_lcc),
			('agents',self._get_agents),
                        ('texts',self._get_text_urls)
		)

	def get_work_id(self):
		'''
		return integer id for work in DB
		'''
		return self._extract_int(self._get_work_ref())

	def get_work_info(self):
		'''
		Main interface, returns nested dictionaries of all the requisite information in this graph
		'''
		try:
			return self._work_info
		except AttributeError:
			self._work_info = {}
			for target,method in self._work_map:
				self._work_info[target] = method()
			return self._work_info

	def _get_text_urls(self):
		'''
		returns set of file urls for the different versions of this text
		'''
		return set(self.objects(subject=self._get_work_ref(),predicate=DCTERMS.hasFormat))

	def _get_work_ref(self):
		'''
		return work URIRef of format PGTERMS.ebook
		'''
		try:
			return self._work_ref
		except AttributeError:
			try:
				self._work_ref = self._tuple_unpack(self.subjects(predicate=RDF.type,object=PGTERMS.ebook))
			except ValueError:
				raise IDError('No valid work reference found.')
			return self._work_ref

	def _get_title(self):
		'''
		returns title as properly decoded string 
		'''
                try:
	            title_ref = self._get_single_object(subject=self._get_work_ref(),predicate=DCTERMS.title)
		    return self._safe_string(title_ref)
                except ValueError: #raised when trying to tuple unpack
                    raise NoTitleError

	def _get_lcsh(self):
		'''
		Uses SPARQL to gather LCSH information, which is then decoded
		Returns list of strings
		'''
		query = '''
			SELECT DISTINCT ?lcsh WHERE {
				?a dcam:memberOf dcterms:LCSH .
				?a rdf:value ?lcsh .
				}
			'''
                lcshs = []
                for r in self.query(query):
                    #break apart, strip, and limit LCSH to 100 characters
                    try:
                         lcshs.extend([s.strip()[:100] for s in self._safe_string(r[0]).split('--')])
                    except AttributeError:
                        continue
                return lcshs
            
	def _get_lcc(self):
		'''
		Uses SPARQL to gather LCC information, which is then decoded
		Returns list of strings
		'''
		query = '''
			SELECT DISTINCT ?lcc WHERE {
				?a dcam:memberOf dcterms:LCC .
				?a rdf:value ?lcc .
				}
			'''
		return [self._safe_string(r[0]) for r in self.query(query)]

	def _extract_int(self,ref):
		'''
		returns integer suffix for URI
		'''
		return int(str(ref).split('/')[-1])

	def _get_agents(self):
		'''
		Returns dictionary of all agents mentioned in work
		'''
		agents = {}
		for agent in self.subjects(predicate=RDF.type,object=PGTERMS.agent):
			agent_id = self._extract_int(agent)
			agents[agent_id] = {}
			for target,predicate_reference,single,callback in self._agent_map:
				method = self._get_single_object if single else self.objects
				try:
					agents[agent_id][target] = callback(method(subject=agent,predicate=predicate_reference))
				except ValueError:
					continue #this info is non-vital, so can continue
		return agents

	def _get_single_object(self,**kwargs):
		'''
		wraps self._tuple_unpack; returns single object if just one object, else ValueError rises through
		'''
		return self._tuple_unpack(set(self.objects(**kwargs)))

	def _tuple_unpack(self,coll):
		'''
		Reduces generator to single item if it only has one item; if more than one item, ValueError rises from here
		'''
		(item,) = coll #this will raise a ValueError if coll doesn't have one member in it
		return item

	def _safe_string(self,ref):
		'''
		Special method to decode unicode literals to string; if UnicodeEncodeError, do some special encoding business
		'''
                #ry:
		#       string = str(ref)
		#xcept UnicodeEncodeError:
		#       #do something
		#       return None
		return unicode(ref) 
#
#def save_pggraphs(pgs):
#       '''
#       writes pggraphs to db as appropriate objects
#       '''
#       lcsh = set()
#       lcc = set()
#       works = {}
#       agents = {}
#
#       for pg in pgs:
#       	info = pg.get_work_info()
#       	works[pg.get_work_id()] = info
#       	lcsh.update(info['lcsh'])
#       	lcc.update(info['lcc'])
#       	agents.update(info['agents'])
#
#       #insert ignore all lcsh, all lcc
#       
