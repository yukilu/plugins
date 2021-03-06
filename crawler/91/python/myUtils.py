import os
import re
import json
import math
import time
import doctest

def find(target, lst, property):
    for o in lst:
        if target == o[property]:
            return o

def read(filename, file_type='json'):
    try:
        data = readFile(filename, file_type=file_type)
    except:
        bakfilename = '%s_bak%s' % os.path.splitext(filename)
        print(f'read {filename} error, read {bakfilename} instead')
        data = readFile(bakfilename, file_type=file_type)
    
    return data

def readFile(filename, file_type='json'):
    with open(filename) as f:
        if file_type == 'json':
            data = json.load(f)
        elif file_type == 'string':
            data = f.read()
    return data

def write(filename, data, indent=0, file_type='json'):
    with open(filename, 'w') as f:
        if file_type == 'json':
            if indent:
                json.dump(data, f, indent=indent)
            else:
                json.dump(data, f)
        elif file_type == 'string':
            f.write(data)
    return True

def copyFrom(originFile, targetFile, indent=0, file_type='json'):
    data = read(originFile, file_type)
    return write(targetFile, data, indent=indent, file_type=file_type)

def backup(filename, indent=0, file_type='json'):
    bak_filename = '%s_bak%s' % os.path.splitext(filename)
    return copyFrom(filename, bak_filename, indent=indent, file_type=file_type)

def handleDomain(domain):
    ''' handle wrong domain string
    >>> handleDomain('/91porn.com/v?a')
    'http://www.91porn.com'
    >>> handleDomain(':/www.91porn.com')
    'http://www.91porn.com'
    >>> handleDomain('   tp://www.91porn.com')
    'http://www.91porn.com'
    '''
    domain = domain.strip()

    if not domain:
        return

    p = re.compile('h?t{0,2}p?s?:?/{0,2}([\w-]+\.)?(\w+\.\w+)/?')
    m = p.match(domain)
    if not m:
        return

    url = m.groups()
    first = url[0] if url[0] else 'www.'
    domain = 'http://' + first + url[1]
    return domain

def handleUrl(url):
    '''handle wrong url
    >>> handleUrl('http://www.91porn.com/v.php?ct=0&vw=nice')
    '/v.php?ct=0&vw=nice'
    >>> handleUrl('http://www.91porn.com/v.php?ct=0&vw=nice&page=2')
    '/v.php?ct=0&vw=nice'
    >>> handleUrl('www.91porn.com/v.php?ct=0&vw=nice')
    '/v.php?ct=0&vw=nice'
    >>> handleUrl('om/v.php?ct=0&vw=nice')
    '/v.php?ct=0&vw=nice'
    >>> handleUrl('/v.php?ct=0&vw=nice')
    '/v.php?ct=0&vw=nice'
    >>> handleUrl('v.php?ct=0&vw=nice')
    '/v.php?ct=0&vw=nice'
    '''
    url = url.strip()

    if not url:
        return

    page_patttern = re.compile('&page=\d+')
    m = page_patttern.search(url)
    if m:
        url = url.replace(m.group(), '')

    pattern1_str = '\.[a-z]+/' # complete domain eg. xx.com/v.php...
    pattern2_str = '[a-z]*/' # incomplete domain eg. om/v.php...

    pattern_strs = [pattern1_str, pattern2_str]

    handled_url = f'/{url}'
    for p_s in pattern_strs:
        p = re.compile(p_s)
        m = p.search(url)
        if m:
            handled_url = url[m.span()[1] - 1:]
            break

    return handled_url

def filterIds(hrefs):
    filteredHrefs = filter(lambda href: href['done'], hrefs)
    return [href['id'] for href in filteredHrefs]

def dictArray2str(dict_list, seperator='\n'):
    '''converse dict list to string list
    >>> dictArray2str([{'a':0}, {'a':1}, {'a':2}])
    '{"a": 0}\\n{"a": 1}\\n{"a": 2}'
    '''
    str_list = [json.dumps(o) for o in dict_list]
    return seperator.join(str_list)

def matchMp4(src):
    '''matchMp4
    >>> matchMp4('http://185.38.13.159//mp43/44132.mp4?st=-5OcpSXvfvhhKfr8CTP4tw&e=1513205133')
    44132
    '''
    pattern = re.compile('(\d+)\.mp4')
    m = pattern.search(src)
    if m:
        return int(m.group(1))

def getFilenamesIntoInt(path=None):
    filenames = [int(os.path.splitext(f)[0]) for f in os.listdir(path)]
    filenames.sort()
    return filenames

def binarySearch(target, lst):
    '''find target index in list
    >>> binarySearch(4, [0,1,2,3,4,5])
    (True, 4)
    >>> binarySearch(1.5, [0,1,2,3,4,5])
    (False, 2)
    >>> binarySearch(5.5, [0,1,2,3,4,5])
    (False, 6)
    >>> binarySearch(-1, [0,1,2,3,4,5])
    (False, 0)
    >>> binarySearch(1, [0])
    (False, 1)
    >>> binarySearch(0, [1])
    (False, 0)
    >>> binarySearch(0, [0])
    (True, 0)
    '''
    is_found = False
    i = 0
    j = len(lst) - 1
    if j == -1:
        raise ValueError('list can not be empty')

    while i <= j:
        m = i + (j - i) // 2
        if (target < lst[m]):
            j = m - 1
        elif (target > lst[m]):
            i = m + 1
        else:
            is_found = True
            i = m
            break
    
    return (is_found, i)

def insertIntoOrdered(target, ordered_list):
    '''insert target into ordered list'''
    if not ordered_list:
        is_found, index = False, 0
    else:
        is_found, index = binarySearch(target, ordered_list)
    
    can_insert = not is_found
    if can_insert:
        ordered_list.insert(index, target)
    return can_insert

def insertIntoOrderedFile(targets, filename):
    '''insert targets list into ordered list from file and write back to file to cover it'''
    ordered_list = read(filename)
    insert_fail = []
    insert_success = []
    for t in targets:
        can_insert = insertIntoOrdered(t, ordered_list)
        if can_insert:
            insert_success.append(t)
        else:
            insert_fail.append(t)
    write(filename, ordered_list)

    return insert_success, insert_fail

def removeInFile(targets, filename):
    lst = read(filename)
    if not lst:
        return

    remove_fail = []
    remove_success = []
    for t in targets:
        try:
            lst.remove(t)
            remove_success.append(t)
        except ValueError as e:
            print(e)
            remove_fail.append(t)
    write(filename, lst)
    return remove_success, remove_fail

def findInFile(targets, filename):
    ordered_list = read(filename)
    if not ordered_list:
        return
    
    found = []
    not_found = []
    for target in targets:
        is_found, _ = binarySearch(target, ordered_list)
        if is_found:
            found.append(target)
        else:
            not_found.append(target)
    return found, not_found

def str2ints(target_str, seperator = ' '):
    target_str = target_str.strip()
    if not target_str:
        return

    try:
        target_strs = target_str.split(seperator)
        targets = [int(target_str) for target_str in target_strs]
        targets.sort()
    except:
        print('handle target_str error in function str2ints in myUtils.py')
        return
    
    return targets

def getTimeStamp():
    return math.floor(time.time())

if __name__ == '__main__':
    doctest.testmod(verbose=True)