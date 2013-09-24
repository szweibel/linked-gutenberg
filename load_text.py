import re

def pretend_callback(work):
    pass

        # extension, file type test, formatting callback for all supported file types
file_types = (
        ('-0.zip',lambda f:'-0.zip' in f,pretend_callback), #zipped unicode
        ('.zip',lambda f: '.zip' in f and not re.search(r'-.*\.zip$',f),pretend_callback), #zipped ASCII
        ('-0.txt',lambda f: '-0.txt' in f,pretend_callback), #unicode
        ('.txt.utf-8',lambda f:'.txt.utf-8' in f,pretend_callback), #utf-8
        ('.txt',lambda f: '.txt' in f and not re.search(r'-.*\.txt$',f),pretend_callback) #ASCII
    )

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

def get_text_list(filenames):
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
    if not return_list: raise Exception('No suitable files found')
    return sorted(natural_sort(return_list),key=lambda f:partial_index(0,f[1],file_types))

def natural_sort(l):  
    '''
    from http://stackoverflow.com/a/4836734/1567452
    '''
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda file_info: [ convert(c) for c in re.split('([0-9]+)', file_info[0])] 
    return sorted(l, key = alphanum_key)

def sort_text_list((text_info)):
    filename,ext,callback = text_info
    return file_types.index((ext,callback))

def partial_index(index,term,tup_of_tups): 
    '''
    search an iterable of iterables looking for a term at a specific index of
    each iterable
    '''
    for i,tup in enumerate(tup_of_tups):
        if tup[index] == term: return i
    raise ValueError('This value doesn\'t exist in any of this iterable\'s tuples') 

if __name__ == '__main__':
    for filename in get_text_list(test_list):
        print filename

