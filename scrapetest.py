# -*-coding:utf-8-*-
# Screippaustesti

import lxml.html as html
import time
import urllib2

cache_ids = {}


def create_id_table():
    url = "http://sports.yahoo.com/nhl/stats/byposition?pos=C,RW,LW,D"
    t0 = time.time()
    page = urllib2.urlopen(url).read()
    t1 = time.time() - t0
    print "Haettiin sivu ajassa", t1

    t0 = time.time()
    root = html.fromstring(page)
    t1 = time.time() - t0
    print "Muokattiin lxml-objektiksi ajassa", t1

    t0 = time.time()
    rows = root.xpath("//tr[@class='ysprow1' or @class='ysprow2']")
    id_table = {}
    for row in rows:
        links = row.xpath(".//a")
        name = links[0].text
        pid = links[0].attrib["href"].split("/")[-1]
        team = links[1].text
        id_table[name.upper()] = dict(id=pid, team=team)
    t1 = time.time() - t0
    print "Objektista parsettiin data ajassa", t1
    return id_table


def main():
    print "Ohjelma nayttaa pelaajan viimeisimman pelin tilastot."
    print "Ladataan pelaajien id:t ja joukkueet..."
    cache_ids = create_id_table()
    while 1:
        query = raw_input("Pelaajan nimi:\r\n>>> ")
        try:
            pid = cache_ids[query.upper().strip()]
            print "Pelaajan %s id on %s" % (query, pid["id"])
        except KeyError:
            print "Nimen tulee olla tasmalleen oikein kirjoitettu."
            continue

if __name__ == "__main__":
    main()
