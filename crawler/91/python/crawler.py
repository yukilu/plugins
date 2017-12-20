from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from pyquery import PyQuery as pq

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'}

def getHref(base_url, domain, page_index, initial_id):
    domain_length = len(domain)

    if page_index > 1:
        page_path = '&page=' + str(page_index)
    else:
        page_path = ''
    url = domain + base_url + page_path

    hrefs = []
    req = Request(url=url, headers=headers)
    html = urlopen(req).read()

    doc = pq(html)
    alist = doc('.listchannel > a[target=blank]')
    hrefs_pq = alist.map(lambda i, a: pq(a).attr('href'))

    for i, h in enumerate(hrefs_pq):
        href = { 'id': initial_id + i, 'itemIndex': i, 'pageIndex': page_index, 'href': h[domain_length:] }
        hrefs.append(href)
    
    return hrefs

def getSrc(url, error_callback):
    src = None
    try:
        req = Request(url=url, headers=headers)
        html = urlopen(req).read()

        doc = pq(html)
        source = doc('source')
        if source:
            src = source.attr('src')
    except HTTPError as e:
        error_callback(e)
    except URLError as e:
        error_callback(e)

    return src