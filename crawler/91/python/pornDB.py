import sqlite3

def initialDB(table, database='pornHref'):
    conn = sqlite3.connect('%s.db' % database)
    c = conn.cursor()
    c.execute('''CREATE TABLE %s
        (ID INT PRIMARY KEY NOT NULL,
        ITEMINDEX INT NOT NULL,
        PAGEINDEX INT NOT NULL,
        HREF CHAR(150))''' % table)
    conn.commit()
    conn.close()
    return True

def readAllHrefs(table, database='pornHref'):
    conn = sqlite3.connect('%s.db' % database)
    c = conn.cursor()
    cursor = c.execute('SELECT * from %s' % table)
    hrefs = []
    for row in cursor:
        href = { 'id': row[0], 'itemIndex': row[1], 'pageIndex': row[2], 'href': row[3], 'done': False }
        hrefs.append(href)
    conn.close()
    return hrefs

def addHrefs(hrefs, table, database='pornHref'):
    conn = sqlite3.connect('%s.db' % database)
    c = conn.cursor()
    for href in hrefs:
        href['table'] = table
        c.execute('INSERT INTO %(table)s(ID,ITEMINDEX,PAGEINDEX,HREF) VALUES(%(id)d,%(itemIndex)d,%(pageIndex)d,"%(href)s")' % href)
    conn.commit()
    conn.close()
    return True

def deleteHrefs(ids, table, database='pornHref'):
    conn = sqlite3.connect('%s.db' % database)
    c = conn.cursor()
    for i in ids:
        c.execute('DELETE from %s where ID=%d' % (table, i))
    conn.commit()
    conn.close()
    return True

def clearHrefs(table, database='pornHref'):
    conn = sqlite3.connect('%s.db' % database)
    c = conn.cursor()
    c.execute('DELETE from %s' % table)
    conn.commit()
    conn.close()
    return True

#if __name__ == '__main__':
    #initialDB()