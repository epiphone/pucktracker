# -*-coding:utf-8-*-
# Screippaustesti

import lxml.html as html
import time

teams = ["njd", "nyi", "nyr", "phi", "pit", "bos", "buf", "mon", "ott", "tor",
         "car", "fla", "tam", "was", "wpg", "chi", "cob", "det", "nas", "stl",
         "cgy", "col", "edm", "min", "van", "ana", "dal", "los", "pho", "san"]
CACHE_IDS = {}
CACHE_GAMES = {}


def scrape_ids():
    """Palauttaa dictionaryn jossa avaimena pelaajan nimi, arvona
    joukkue, id ja koko kauden tilastot."""
    global CACHE_IDS
    if CACHE_IDS:
        return CACHE_IDS

    url = "http://sports.yahoo.com/nhl/stats/byposition?pos=C,RW,LW,D"
    t0 = time.time()
    root = html.parse(url)
    t1 = time.time() - t0
    print "Haettiin html ja muokattiin lxml-objektiksi ajassa", t1

    t0 = time.time()
    ids = {}
    rows = root.xpath("//table[count(tr)>10]/tr")
    columns = [el.text_content().strip().lower() for el in rows[0].xpath("td[*]")]
    columns = columns[1:]
    for row in rows[1:]:
        name = row.xpath("td/a")[0].text_content().lower()
        pid = row.xpath("td/a")[0].attrib["href"].split("/")[-1]
        stats = {"pid": pid}
        i = 0
        for td in row.xpath("td")[1:]:
            text = td.text_content().strip()
            if text != "":
                stats[columns[i]] = text
                i += 1
        ids[name] = stats

    t1 = time.time() - t0
    print "Objektista parsettiin data ajassa", t1

    CACHE_IDS = ids
    return ids


def scrape_played_games(team, season="2013"):
    """Palauttaa dictionaryn jossa avaimena joukkueen PELATTUJEN otteluiden
    id:t, arvona ottelun 'nimi' (esim. Boston Bruins vs Winnipeg Jets)."""
    if not team.lower() in teams:
        raise Exception("Virheellinen joukkueen nimi.")

    # Jos ottelut löytyvät välimuistista, palautetaan se:
    if team in CACHE_GAMES:
        return CACHE_GAMES[team]

    # Muuten skreipataan otteluohjelma ja tallennetaan välimuistiin:
    url = """http://sports.yahoo.com/nhl/teams/%s
          /schedule?view=print_list&season=%s""" % (team, season)
    t0 = time.time()

    root = html.parse(url)
    rows = root.xpath("//ul/li[position()>4]//table/tbody/tr")
    games = {}
    for row in rows:
        href = row.xpath("td[3]/a")[0].attrib["href"]
        if not "recap?gid=" in href:
            break
        gid = href.split("gid=")[-1]  # TODO entä jos gid:n jälkeen toinen parametri?
        games[gid] = row.xpath("td")[1].text_content().strip()

    t1 = time.time() - t0
    print "Haettiin html ja parsettiin ajassa", t1

    # Oikeasti tällä välimuistilla olisi jonkinlainen umpeutumisaika.
    CACHE_GAMES[team] = games
    return games


def get_latest_game(team):
    """Palauttaa joukkueen viimeisimmän pelatun pelin id:n."""
    return sorted(scrape_played_games(team))[-1]


def get_pid(name):
    """Palauttaa nimeä vastaavan id:n tai listan suosituksista, jos nimeä
    ei löydy."""
    name = name.lower().strip()
    ids = scrape_ids()
    try:
        return ids[name]["pid"]
    except KeyError:
        suggestions = {}
        for key in ids:
            if name in key:
                suggestions[key] = ids[key]["pid"]
        return suggestions
