import re, requests, nltk
from gute import Work
from zipfile import ZipFile
from StringIO import StringIO
from urlparse import urlparse
from os.path import basename,splitext

# POST-DOWNLOAD CALLBACKS
def get_file_within_zip(url,content):
    filename,extension = splitext(basename(urlparse(url).path))     
    return unzip_file(filename+'.txt',content)

def placeholder_callback(url,content):
    return content

def unzip_file(filename,content):
    '''
    Unzip file -- will raise KeyError if file not present
    '''
    z = ZipFile(StringIO(content))
    return z.read(filename)

# SUITABLE FILE TYPES AND THEIR RELATED FUNCTIONS
# extension, file type test, formatting callback for all supported file types 
# each callback receives both the url  and the file contentt
file_types = ( 
        ('-0.zip',lambda f:'-0.zip' in f,get_file_within_zip),#zipped unicode
        ('.zip',lambda f: '.zip' in f and not re.search(r'-.*\.zip$',f),get_file_within_zip), #zipped ASCII
        ('-0.txt',lambda f: '-0.txt' in f,placeholder_callback), #unicode
        ('.txt.utf-8',lambda f:'.txt.utf-8' in f,placeholder_callback), #utf-8
        ('.txt',lambda f: '.txt' in f and not re.search(r'-.*\.txt$',f),placeholder_callback) #ASCII
    )

class CorpusDownloadError(Exception):
    pass

class SuitableFileError(Exception):
    pass

#WORKFLOW FUNCTIONS
def process_corpera(work):
    '''
    This is the main process -- it downloads the text, tokenizes it, and 
    loads it into the database
    '''
    return download_corpus(t.url for t in work.texts)

def download_corpus(filenames):
    '''
    This function takes a list of urls (such as those offered on the model Work),
    sorts them by suitability and preference (e.g. perhaps preferring zipped files and 
    particular encodings), attempts to download them, calls the designated callback 
    for the file type (e.g. unzipping), and returns the actual corpus of the text 
    (or raises a download error exception).
    '''
    suitable_files = get_suitable_files(filenames) 
    for url,ext,callback in suitable_files:
        print 'Trying '+url
        try:
            dled = download_file(url)
        except requests.exceptions.HTTPError as e:
            print 'Downloading '+url+' failed with a '+str(e.errno)+'status code'
            continue 
        try:
            formatted = callback(url,dled) 
        except Exception as e:
            print 'Formatting callback failed for '+url+': '+e
            continue
        assert formatted  
        return formatted
    raise CorpusDownloadError('Unable to download from any of the suitable links') 

# TEST DATA
test_list = [
    '1/2/3/4/12345/12345.txt',
    '1/2/3/4/12345/12345.zip',
    '1/2/3/4/12345/12345-0.txt',
    '1/2/3/4/12345/12345-0.zip',
    '1/2/3/4/12345/12345-8.txt',
    '1/2/3/4/12345/12345-8.zip',
    '1/2/3/4/12345/12345-h.zip',
    '1/2/3/4/12345/12345-hp.zip',
    '1/2/3/4/12345/12345-t.zip',
    '1/2/3/4/12345/12345-x.zip',
    '1/2/3/4/12345/12345-pdf.pdf',
    '1/2/3/4/12345/12345-pdf.zip',
    '1/2/3/4/12345/12345-lit.lit',
    '1/2/3/4/12345/12345-lit-readme.lit',
    '1/2/3/4/12345/12345-lit.zip'
    ]

# TEXT LIST MANIPULATION
def get_suitable_files(filenames):
    ''' 
    This function takes a list of texts and removes inappropriate ones while
    ordering them by preference based on naming conventions described here:
    http://www.gutenberg.org/wiki/Gutenberg:Readers'_FAQ#R.35._What_do_the_filenames_of_the_texts_mean.3F
    '''
    return_list = []
    for filename in filenames:
        for ext,test,callback in file_types:
            if test(filename):
                return_list.append((filename,ext,callback))
                break
    if not return_list: raise SuitableFileError('No suitable files found')
    return sorted(natural_file_sort(return_list),key=lambda f:partial_index(0,f[1],file_types))

def natural_file_sort(l):  
    '''
    from http://stackoverflow.com/a/4836734/1567452 but added the extra step
    of removing the file extension.
    '''
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda file_info: [ convert(c) for c in re.split('([0-9]+)', file_info[0].replace(file_info[1],''))] 
    return sorted(l, key = alphanum_key)

def partial_index(index,term,tup_of_tups): 
    '''
    search an iterable of iterables looking for a term at a specific index of
    each iterable
    '''
    for i,tup in enumerate(tup_of_tups):
        if tup[index] == term: return i
    raise ValueError('This value doesn\'t exist in any of this iterable\'s tuples') 

# Download functions
def download_file(url):
    '''
    Process for downloading file
    '''
    r = requests.get(url)
    r.raise_for_status()
    print 'Downloaded '+url
    return r.content

if __name__ == '__main__':
    import sys
    works = Work.query.filter(Work.id.in_(sys.argv[1:])).all()
    for work in works:
         print process_corpera(work)[:200]
