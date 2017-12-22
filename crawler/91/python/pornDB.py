import sqlite3

def initialDB(table, database='pornHref'):
    conn = sqlite3.connect('%s.db' % database)
    cur = conn.cursor()
    cur.execute(f'''CREATE TABLE {table}
        (ID INT PRIMARY KEY NOT NULL,
        ITEMINDEX INT NOT NULL,
        PAGEINDEX INT NOT NULL,
        HREF CHAR(150))''')
    cur.close()
    conn.commit()
    conn.close()
    return True

def readAllHrefs(table, database='pornHref'):
    conn = sqlite3.connect(f'{database}.db')
    cur = conn.cursor()
    cur.execute(f'SELECT * from {table}')
    hrefs = []
    for row in cur:
        href = { 'id': row[0], 'itemIndex': row[1], 'pageIndex': row[2], 'href': row[3], 'done': False }
        hrefs.append(href)
    cur.close()
    conn.close()
    return hrefs

def addHrefs(hrefs, table, database='pornHref'):
    insert_template = 'INSERT INTO %(table)s(ID,ITEMINDEX,PAGEINDEX,HREF) VALUES(%(id)d,%(itemIndex)d,%(pageIndex)d,"%(href)s")'

    conn = sqlite3.connect(f'{database}.db')
    cur = conn.cursor()
    for href in hrefs:
        href['table'] = table
        cur.execute(insert_template % href)
    cur.close() 
    conn.commit()
    conn.close()
    return True

def deleteHrefs(ids, table, database='pornHref'):
    conn = sqlite3.connect('%s.db' % database)
    cur = conn.cursor()
    for i in ids:
        cur.execute(f'DELETE from {table} where ID={i}')
    cur.close()
    conn.commit()
    conn.close()
    return True

def clearHrefs(table, database='pornHref'):
    conn = sqlite3.connect(f'{database}.db')
    cur = conn.cursor()
    cur.execute(f'DELETE from {table}')
    cur.close()
    conn.commit()
    conn.close()
    return True

#if __name__ == '__main__':
    #initialDB()