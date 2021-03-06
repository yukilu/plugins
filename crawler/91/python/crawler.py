from urllib.request import Request, urlopen
from urllib.parse import quote
from urllib.error import URLError, HTTPError
from pyquery import PyQuery as pq
import string

import myUtils

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'

cookie = None
cookie_json = None

try:
    cookie_json = myUtils.read('cookie.json')
except FileNotFoundError as e:
    print(e)
except:
    print('read cookie error')

if cookie_json and 'cookie' in cookie_json:
    cookie = cookie_json['cookie']

if cookie:
    headers = { 'User-Agent': user_agent, 'Cookie': cookie }
    print('get cookie')
else:
    headers = { 'User-Agent': user_agent }
    print('no cookie')

def getHref(base_url, domain, page_index, initial_id):
    #selector_a = '.listchannel > a[target=blank]'
    selector_a = 'div[class*=imagechannel] > a'
    node_attr = 'href'

    domain_length = len(domain)
    base_url = quote(base_url, safe=string.printable)

    if page_index > 1:
        page_path = '&page=' + str(page_index)
    else:
        page_path = ''
    
    url = f'{domain}{base_url}{page_path}'
    #print(url)

    hrefs = []
    req = Request(url=url, headers=headers)
    html = urlopen(req).read()

    #with open('f.txt', 'w') as f:
        #f.write(html.decode('utf-8'))

    doc = pq(html)
    alist = doc(selector_a)
    hrefs_pq = alist.map(lambda i, a: pq(a).attr(node_attr))

    for i, h in enumerate(hrefs_pq):
        href = { 'id': initial_id + i, 'itemIndex': i, 'pageIndex': page_index, 'href': h[domain_length:] }
        hrefs.append(href)
    
    if not hrefs:
        raise ValueError('hrefs is empty [f=getHref, module=crawler.py]')

    return hrefs

def getSrc(url, error_callback):
    selector = 'source'
    node_attr = 'src'

    url = quote(url, safe=string.printable)

    value = None
    try:
        req = Request(url=url, headers=headers)
        html = urlopen(req).read()

        doc = pq(html)
        node = doc(selector)
        if node:
            value = node.attr(node_attr)
    except HTTPError as e:
        print(e)
        error_callback(e)
    except URLError as e:
        print(e)
        error_callback(e)
    except ConnectionError as e:
        print(e)
        error_callback(e)
    except:
        print('other net error')

    return value