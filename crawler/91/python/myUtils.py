import re
import json
import doctest

def find(target, array, property):
    for o in array:
        if target == o[property]:
            return o

def read(filename, type='json'):
    try:
        with open(filename) as f:
            if type == 'json':
                data = json.load(f)
            elif type == 'string':
                data = f.read()
    except FileNotFoundError as e:
        print(e)
        return

    return data

def write(filename, data, type='json'):
    with open(filename, 'w') as f:
        if type == 'json':
            json.dump(data, f, indent=2)
        elif type == 'string':
            f.write(data)
    return True

def handleDomain(domain):
    ''' handle wrong domain string
    >>> handleDomain('htp:/91porn.com/v?a')
    'http://www.91porn.com'
    >>> handleDomain('91porn.com')
    'http://www.91porn.com'
    >>> handleDomain('http://www.91porn.com')
    'http://www.91porn.com'
    '''
    domain = domain.strip()
    p = re.compile('(?:[\w]*:?/{1,2})?([\w]+\.)?([\w]+\.[\w]+)(?:/[\w]*)?')
    m = p.match(domain)
    if m:
        url = m.groups()
        first = url[0] if url[0] else 'www.'
        domain = 'http://' + first + url[1]
    return domain

def filterIds(hrefs):
    filteredHrefs = filter(lambda href: href['done'], hrefs)
    return [href['id'] for href in filteredHrefs]

def dictArray2str(array, seperator='\n'):
    '''converse dict array to string array
    >>> dictArray2str([{'a':0}, {'a':1}, {'a':2}])
    '{"a": 0}\\n{"a": 1}\\n{"a": 2}'
    '''
    strArray = list(map(lambda o: json.dumps(o), array))
    return seperator.join(strArray)

if __name__ == '__main__':
    doctest.testmod(verbose=True)