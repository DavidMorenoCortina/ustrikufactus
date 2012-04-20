import urllib.request
from bs4 import BeautifulSoup
try:  
    import cPickle as pickle  
except ImportError:  
    import pickle

""" Maintenance """
def deleteLinksGroup(index, needle):
    for elem in index:
        if elem[0].find(needle)==0:
            index.remove(elem)

def deleteLink(index, needle):
    for elem in index:
        if elem[0] == needle:
            index.remove(elem)

""" Searcher """
def DuplicateList(lista): # Duplicate a list
    result = []
    for i in lista:
        positions = []
        for pos in i[1]:
            positions.append(pos)
        result.append([i[0], positions])
    return result

def UrlsOnlyInBoth(list1, list2, keyword):
    result = []
    for i in list1:
        for j in list2:
            listadoPosiciones = []
            if i[0] == j[0]:
                for pos1 in range(0, len(i[1])):
                    if i[1][pos1] >-1:
                        for pos2 in range(0, len(j[1])):
                            if j[1][pos2] >-1:
                                aux = i[1][pos1] + len(keyword) + 1
                                if aux == j[1][pos2]:
                                    listadoPosiciones.append(j[1][pos2])
                        
                        
                        
                if len(listadoPosiciones) > 0: 
                    result.append(j)
                    result[-1][1] = listadoPosiciones
    return result

def multi_lookup(index, query):
    words = query.split()
    simpleSearch = []
    multiSearch = []
    
    # First keyword
    keywordPrev = words[0]
    keyword = words[0]
    if keyword in index:
        multiSearch = DuplicateList(index[keyword])
        for link in index[keyword]:
            if link[0] not in simpleSearch:
                simpleSearch.append(link[0])

    # the remaining keywords
    multiple = True
    for i in range(1, len(words)):
        keyword = words[i]
        if keyword in index:
            for link in index[keyword]:
                if link[0] not in simpleSearch:
                    simpleSearch.append(link[0])
        else:
            multiple = False
        if multiple:
            listAux = DuplicateList(index[keyword])
            multiSearch = UrlsOnlyInBoth(multiSearch, listAux, keywordPrev)
            keywordPrev = keyword
        else:
            multiSearch = []
    resultsMultiSearch = []
    for e in multiSearch:
        resultsMultiSearch.append(e[0])
    resultsSimpleSearch = []
    for e in simpleSearch:
        if e not in resultsMultiSearch:
            resultsSimpleSearch.append(e)
    return resultsMultiSearch, resultsSimpleSearch

def search(index, query):
    resultMulti, resultSimple = multi_lookup(index, query.lower())
    print("")
    print("")
    print('RESULTS FOR "'+query+'"')
    for e in resultMulti:
        print(e)
    if resultSimple:
        print("")
        print("Additional results that might be useful after the above ones:")
        for e in resultSimple:
            print(e)

""" Crawler """
def get_page(url):
    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        a = opener.open(url)
        if str(a.info()).find('Content-Type: image/') > -1:
            content = ""
        else:
            content = a.read().decode('utf-8')
    except:
        content = ""
    return BeautifulSoup(content)
        
        



def union(a, b):
    for e in b:
        if e not in a:
            a.append(e)

def add_page_to_index(index, url, content):
    text = content.get_text().lower()
    words = text.split()
    for word in words:
        pos = []
        auxPos = 0
        while auxPos > -1:
            auxPos = text.find(word, auxPos)
            if auxPos>-1:
                pos.append(auxPos)
                auxPos+=1
        add_to_index(index, word, url, pos)
        
def add_to_index(index, keyword, url, pos):
    if keyword in index:
        for i in index[keyword]:
            if i[0] == url:
                return
        index[keyword].append([url, pos])
    else:
        index[keyword] = [[url, pos]]

def separateLinks(outlinks, baseDomain, internalLinksToAvoid):
    intLinks = []
    extLinks = []
    allLinks = []
    for link in outlinks:
        aux = str(link.get('href'))
        if (aux.find('http://')==0 or aux.find('www.')==0) and aux.find(baseDomain)==-1:
            extLinks.append(aux)
            allLinks.append(aux)
        else:
            if aux.find(baseDomain)==-1:
                okUrl = True
                url = baseDomain+aux
                for e in internalLinksToAvoid:
                    if url.find(e)==0:
                        okUrl = False
                if okUrl:
                    intLinks.append(url)
                    allLinks.append(url)
            else:
                okUrl = True
                for e in internalLinksToAvoid:
                    if aux.find(e)==0:
                        okUrl = False
                if okUrl:
                    intLinks.append(aux)
                    allLinks.append(aux)
    return intLinks, extLinks, allLinks

def LoadIndexAndGraph():
    try:
        f = open("ustrikufactus_index.dat", 'rb')
        try:
            index = pickle.load(f)
        except EOFError:
            index = {}
        f.close()
    except IOError:
        index = {}
    
    # graph := <url>, [list of pages it links to]
    try:
        f = open("ustrikufactus_graph.dat", 'rb')
        try:
            graph = pickle.load(f)
        except EOFError:
            graph = {}
        f.close()
    except IOError:
        graph = {}

    try:
        f = open("ustrikufactus_crawled.dat", 'rb')
        try:
            crawled = pickle.load(f)
        except EOFError:
            crawled = []
        f.close()
    except IOError:
        crawled = []
    return index, graph, crawled

def SaveIndexAndGraph(index, graph, crawled):
    f = open("ustrikufactus_index.dat", "wb")
    pickle.dump(index, f)
    f.close()

    f = open("ustrikufactus_graph.dat", "wb")
    pickle.dump(graph, f)
    f.close()

    f = open("ustrikufactus_crawled.dat", "wb")
    pickle.dump(crawled, f)
    f.close()

def crawlSite(seed, baseDomain, internalLinksToAvoid):
    return crawl(seed, baseDomain, True, internalLinksToAvoid)

def crawlLink(seed, baseDomain):
    return crawl(seed, baseDomain, False, [])



def crawl(seed, baseDomain, fullSite, internalLinksToAvoid): # returns index, graph of inlinks and list of links to other sites founded in seed
    tocrawl = [seed]
    notToCrawl = [] 
    outlinks = ''
    index, graph, crawled = LoadIndexAndGraph()
    while tocrawl: 
        page = tocrawl.pop()
        if page not in crawled:
            content = get_page(page)
            add_page_to_index(index, page, content)
            outlinks = content.find_all('a')
            internalLinks, externalLinks, allLinks = separateLinks(outlinks, baseDomain, internalLinksToAvoid)
            graph[page] = allLinks
            union(notToCrawl, externalLinks)
            if fullSite:
                union(tocrawl, internalLinks)
            crawled.append(page)
    SaveIndexAndGraph(index, graph, crawled)
    return index, graph, notToCrawl

""" Menu """
def ShowMenu():
    print("WELCOME TO USTRIKUFACTUS SEARCHER!")
    print("")
    print(" - To indexing a complete site type:")
    print("        index, graph, notToCrawl = crawlSite(StarterLink, domain, [internalLinksToAvoid])")
    print("")
    print(" - To indexing a unique link:")
    print("        index, graph, notToCrawl = crawlLink(StarterLink, domain)")
    print("     This is useful to index parts of a big webpage. For example to index 'http://en.wikipedia.org/wiki/History_of_Rome'")
    print("")
    print(" - To search:")
    print("        search(index, needle)")
    print("")
    print(" - To delete a link:")
    print("        deleteLink(index, needle)")
    print("")
    print(" - To delete all links starting with:")
    print("        deleteLinksGroup(index, needle)")
    print("")
    print("")
    print("Remember this program is stored at your own computer.")
    print("DON'T USE 'crawlSite' WITH BIG SITES.")
    print("IT'LL WILL DEMOLISH ALL HARD DISK FROM YOUR COMPUTER.")
    
    

ShowMenu()
index, graph, externalLinks = crawlLink('', '')

