# -*-coding:utf-8-*-
"""
Scraper NHL-tilastoja varten.

Käytettävät sivut:
- sports.yahoo.com
- nhl.com

Yleisesti funktiot palauttavat
- tyhjän tietorakenteen, jos skreippaus onnistuu mutta dataa ei löydy,
- tyhjiöarvon None jos skreipattavan sivun hakeminen epäonnistuu
- ja poikkeuksen, jos skreippaaminen epäonnistuu.

Google App Enginen kautta käytettäessä skreipperi hyödyntää
App Enginen memcached-välimuistia.


author: Aleksi Pekkala
"""

from lxml import html
import time
from datetime import datetime, timedelta
import logging
import sys
import re
try:
    from flask.ext.pytz import timezone
except ImportError:
    import sys
    sys.path.append("..")
    from pytz import timezone
try:
    from google.appengine.api import urlfetch, memcache
    from google.appengine.ext import deferred
except ImportError:
    # Jos scraperia käytetään App Enginen ulkopuolella, luodaan App Enginen
    # ominaisuuksia vastaavat dummy-luokat jotta testaaminen onnistuu:
    import urllib2

    class Urlfetch:
        """Dummy-luokka scraperin testaamiseksi ilman App Engineä."""
        def fetch(self, url):
            response = urllib2.urlopen(url)

            class Response:
                def __init__(self, content, status_code):
                    self.content = content
                    self.status_code = status_code
            return Response(response.read(), response.getcode())

    class Memcache:
        """Dummy-luokka scraperin testaamiseksi ilman App Engineä."""
        def get(self, key):
            pass

        def set(self, key, value, expires=None):
            pass

    class Deferred:
        """Dummy-luokka scraperin testaamiseksi ilman App Engineä."""
        def defer(self, *args, **kwargs):
            pass

    urlfetch = Urlfetch()
    memcache = Memcache()
    deferred = Deferred()

logging.getLogger().setLevel(logging.DEBUG)


### GLOBAALIT MUUTTUJAT ###

LOGGING_ENABLED = True
URL_YAHOO = "http://sports.yahoo.com/nhl"
SEASON = "2012"
MONTHS = ["", "jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]
CONFERENCES = ["east", "west"]
DIVISIONS = ["atlantic", "northeast", "southeast",
             "central", "northwest", "pacific"]
TEAMS = ["njd", "nyi", "nyr", "phi", "pit", "bos", "buf", "mon", "ott", "tor",
         "car", "fla", "tam", "was", "wpg", "chi", "cob", "det", "nas", "stl",
         "cgy", "col", "edm", "min", "van", "ana", "dal", "los", "pho", "san"]
# Uratilastoissa käytetään eri joukkuetunnuksia:
ALT_TEAMS = {"sj": "san", "tb": "tam", "nsh": "nas", "cls": "cob", "la": "los",
             "anh": "ana"}

CITIES = ["new jersey", "ny islanders", "ny rangers", "philadelphia",
          "pittsburgh", "boston", "buffalo", u"montréal", "ottawa", "toronto",
          "carolina", "florida", "tampa bay", "washington", "winnipeg",
          "chicago", "columbus", "detroit", "nashville", "st. louis",
          "calgary", "colorado", "edmonton", "minnesota", "vancouver",
          "anaheim", "dallas", "los angeles", "phoenix", "san jose"]
GOALIE_STATS = ["name", "team", "gp", "gs", "min", "w", "l", "otl", "ega",
                "ga", "gaa", "sa", "sv", "sv%", "so"]
PLAYER_STATS = ["name", "team", "gp", "g", "a", "pts", "+/-", "pim", "hits",
                "bks", "fw", "fl", "fo%", "ppg", "ppa", "shg", "sha", "gw",
                "sog", "pct"]
GOALIE_STAT_DEFAULT = "w"
PLAYER_STAT_DEFAULT = "pts"


### SKREIPPAUSFUNKTIOT ###

def log_done(func, t0, t1, *args):
    if LOGGING_ENABLED:
        params = ", ".join(map(str, args)) if args else ""
        logging.info("[SCRAPER] %s(%s) - LOADED IN %.2fs, SCRAPED IN %.2fs" %
            (func, params, t0, t1))


def scrape_players(query=""):
    """
    Skreippaa kaikki pelaajat, joiden nimi vastaa hakuehtoa. Oletuksena
    haetaan kaikki pelaajat.

    Paluuarvona dictionary, jossa
    avain = pelaajan id,
    arvo = dictionaryssa nimi, joukkue ja pelipaikka.
    """
    # Siistitään hakuehtoa:
    query = re.sub("\s+", " ", query.strip().lower())

    # Tarkistetaan välimuisti:
    players = memcache.get("players")
    if players is not None:
        return {k: v for k, v in players.items() if query in v["name"].lower()}

    # Ladataan skreipattava sivu:
    url = URL_YAHOO + "/players?type=lastname&first=1&query="
    t0 = time.time()
    try:
        response = urlfetch.fetch(url)
        t0 = time.time() - t0
        if response.status_code != 200:
            return None
    except:
        return None

    # Skreipataan:
    t1 = time.time()
    root = html.fromstring(response.content)
    rows = root.xpath("//table//tr[contains(@class, 'ysprow') and count(td)=3]")
    players = {}
    for row in rows:
        tds = row.getchildren()
        pid = tds[0].getchildren()[0].attrib["href"].split("/")[-1]
        name = tds[0].text_content().strip()
        pos = tds[1].text
        team = tds[2].getchildren()[0].attrib["href"].split("/")[-1]
        players[pid] = dict(name=name, pos=pos, team=team)

    # Logataan ja tallennetaan hakutulokset välimuistiin:
    t1 = time.time() - t1
    log_done("scrape_players", t0, t1, query)
    memcache.set("players", players, 60 * 60 * 24)

    return {k: v for k, v in players.items() if query in v["name"].lower()}


def scrape_player_stats(year=SEASON, playoffs=False, goalies=False,
    order="pts", reverse=True):
    """
    Skreippaa valitun kauden kaikki pelaajat tilastoineen.

    Jos goalies-muuttuja on True, haetaan maalivahdit.

    Paluuarvona lista dictionaryjä, joissa
    pelaajan id, nimi, joukkue ja kauden tilastot.
    """
    if goalies:
        pos = "G"
        columns = GOALIE_STATS
        if not order or order not in GOALIE_STATS:
            order = GOALIE_STAT_DEFAULT
        cache_key = "pstats_goalies"
    else:
        pos = "C,RW,LW,D"
        columns = PLAYER_STATS
        if not order or order not in PLAYER_STATS:
            order = PLAYER_STAT_DEFAULT
        cache_key = "pstats_players"

    cache_key += year
    cache_key += "_playoffs" if playoffs else ""

    # Järjestysfunktio
    sort_func = lambda x: -999 if x[order] is None else x[order]

    pstats = memcache.get(cache_key)
    if pstats is not None:
        return sorted(pstats, key=sort_func, reverse=reverse)

    if int(year) > int(SEASON):
        return None

    url = URL_YAHOO + "/stats/byposition?pos=%s&year=%s"
    year = "postseason_" + year if playoffs else "season_" + year
    t0 = time.time()
    try:
        response = urlfetch.fetch(url % (pos, year))
        t0 = time.time() - t0
        if response.status_code != 200:
            return None
    except:
        return None

    t1 = time.time()
    root = html.fromstring(response.content)
    rows = root.xpath("//tr[contains(@class, 'ysprow')]")
    stats = []
    for row in rows:
        stat = {}
        stat["pid"] = row.xpath("*[1]//@href")[0].split("/")[-1]
        columns_iter = iter(columns)
        for td in row.iterchildren():
            stat_value = td.text_content().strip().lower()
            if stat_value:
                if stat_value.isdigit() or stat_value.startswith("-"):
                    stat_value = int(stat_value)
                elif stat_value.startswith("."):
                    stat_value = float(stat_value)
                elif stat_value == "n/a":
                    stat_value = 0.0
                stat[columns_iter.next()] = stat_value
        stats.append(stat)

    t1 = time.time() - t1
    memcache.set(cache_key, stats, 60 * 15)
    log_done("scrape_players", t0, t1, year, playoffs, goalies)
    return sorted(stats, key=sort_func, reverse=reverse)


def scrape_career(pid):
    """
    Skreippaa pelaajan kausittaiset tilastot sekä uran kokonaistilastot.

    Paluuarvona dictionary, jossa avaimina vuodet ja "career", arvoina
    dictionary jossa kauden tilastot.
    """
    # Haetaan välimuistista:
    career = memcache.get("stats_" + pid)
    if career is not None:
        return career

    # Ei löydy välimuistista, skreipataan:
    url = URL_YAHOO + "/players/%s/career" % pid
    t0 = time.time()
    try:
        response = urlfetch.fetch(url)
        t0 = time.time() - t0
        if response.status_code != 200:
            return None
    except:
        return None

    t1 = time.time()
    root = html.fromstring(response.content)

    try:
        header = root.xpath("//tr[@class='ysptblthbody1']")[0]
    except IndexError:
        # ID on virheellinen, tai pelaaja ei ole pelannut yhtään NHL-ottelua:
        return {}

    columns = [td.text.strip().lower() for td in header.getchildren()[1:-1]]
    seasons = {}

    for row in root.xpath("//tr[contains(@class, 'ysprow')]"):
        season = {}
        tds = row.iterchildren()
        year = tds.next().text_content().strip().split("-")[0].lower()
        for col in columns:
            season[col] = parse_stat_value(tds.next())
        seasons[year] = season

    t1 = time.time() - t1
    log_done("scrape_career", t0, t1, pid)
    check = seasons["career"]["gp"]
    # Deferred kutsuu add_cache-funktiota asynkronisesti:
    deferred.defer(add_cache, key="stats_" + pid, value=seasons, check=check)
    return seasons


def scrape_games_by_player(pid, year=SEASON):
    """
    Skreippaa pelaajan valittuna kautena pelatut pelit.

    Paluuarvona dictionary, jonka avaimena ottelun id,
    arvona pelaajan tilastot kyseisestä pelistä.
    """
    pid = str(pid)
    if int(year) > int(SEASON):
        return {}

    games = memcache.get("games_" + pid + year)
    if games:
        return games

    url = URL_YAHOO + "/players/%s/gamelog?year=%s" % (pid, year)
    t0 = time.time()
    try:
        response = urlfetch.fetch(url)
        t0 = time.time() - t0
        if response.status_code != 200:
            return None
    except:
        return None

    t1 = time.time()
    root = html.fromstring(response.content)
    # Parsitaan tilastokolumnit ("g", "a", jne.):
    header = root.xpath("//tr[@class='ysptblthbody1']")[0]
    columns = [td.text.strip().lower() for td in header.getchildren()[1:-1]]

    games = {}
    rows = root.xpath("//table/tr[contains(@class, 'ysprow') and position() < last()]")
    for row in rows:
        gid = row.xpath("td/a/@href")[0].split("gid=")[-1]
        game = {}
        for i, td in enumerate(row.xpath("td")[1:-1]):
            game[columns[i]] = parse_stat_value(td)

        games[gid] = game

    t1 = time.time() - t1
    log_done("scrape_games_by_player", t0, t1, pid, year)
    check = len(games)
    deferred.defer(add_cache, key="games_" + pid + year, value=games,
        check=check)
    return games


def scrape_games_by_team(team, year=SEASON):
    """
    Skreippaa joukkueen kautena pelatut ottelut.

    Palauttaa dictionaryn jossa avaimina otteluiden id:t,
    arvoina vastustaja ja loppulukemat.
    """
    team = team.lower()
    if not team in TEAMS or int(year) > int(SEASON):
        return {}

    games = memcache.get("games_" + team + year)
    if games:
        return games

    url = URL_YAHOO + "/teams/%s/schedule?view=print_list&season=%s" % (team,
        year)
    t0 = time.time()
    try:
        response = urlfetch.fetch(url)
        t0 = time.time() - t0
        if response.status_code != 200:
            return None
    except:
        return None

    t1 = time.time()
    root = html.fromstring(response.content)
    rows = root.xpath("//tbody/tr[td[3]/a[contains(@href, 'recap')]]")
    games = {}
    for row in rows:
        game = {}
        tds = row.getchildren()
        game["opponent"] = tds[1].text_content().strip()
        game["score"] = tds[2].text_content().strip()
        gid = tds[2].xpath("a/@href")[0].split("gid=")[-1]
        games[gid] = game

    t1 = time.time() - t1
    log_done("scrape_games_by_team", t0, t1, team, year)
    check = len(games)
    deferred.defer(add_cache, key="games_" + team + year, value=games,
        check=check)
    return games


def scrape_game(gid):
    """
    Skreippaa yksittäisen ottelun tiedot.

    Palauttaa dictionaryn, jossa joukkueet, pelaajakohtaiset tilastot,
    maalit, shootout-tilastot, sekä ottelun loppulukemat.
    """
    game = memcache.get(gid)
    if game:
        return game

    url = URL_YAHOO + "/boxscore?gid=" + gid
    t0 = time.time()
    try:
        response = urlfetch.fetch(url)
        t0 = time.time() - t0
        if response.status_code != 200:
            return None
    except:
        return None

    t1 = time.time()
    root = html.fromstring(response.content)
    game = {}

    # Ottelun joukkueet ja tulos:
    game["away_team"] = root.xpath("//div[@class='away']//a/@href")[0].split("/")[-1]
    game["home_team"] = root.xpath("//div[@class='home']//a/@href")[0].split("/")[-1]
    game["away_score"] = root.xpath("//div[@class='away']/*")[0].text_content().strip()
    game["home_score"] = root.xpath("//div[@class='home']/*")[0].text_content().strip()

    # Varsinaisen peliajan ja mahd. jatkoajan maalit:
    periods = root.xpath("(//div[count(h5)>2])[1]/table")
    goals, shootout = [], []
    for i, period in enumerate(periods[:4]):
        for tr in period.xpath("tbody/tr[count(td)>3]"):
            tds = tr.xpath("td")
            goal = {}
            goal["period"] = i + 1
            goal["time"] = tds[0].text_content().strip()
            goal["team"] = tds[1].xpath("a/@href")[0].split("/")[-1]
            goal["desc"] = tds[2].text_content().strip()
            goal["score"] = tds[3].text_content().strip()
            goals.append(goal)
    # Shootoutin maalit:
    if len(periods) == 5:
        for tr in periods[4].xpath("tbody/tr"):
            attempt = {}
            attempt["team"] = tr.xpath("td/a/@href")[0].split("/")[-1]
            attempt["desc"] = tr.xpath("td[last()]")[0].text_content().strip()
            shootout.append(attempt)
    game["goals"], game["shootout"] = goals, shootout

    # Pelaajakohtaiset tilastot:
    all_goalies = root.xpath("//div[contains(@class, 'goalies')]/table")
    all_skaters = root.xpath("//div[contains(@class, 'skaters')]/table")
    goalie_cols = all_goalies[0].xpath("thead/tr/th")[1:]
    skater_cols = all_skaters[0].xpath("thead/tr/th")[1:]

    goalies, skaters = {}, {}
    for i, team in enumerate(["away", "home"]):
        # Maalivahdit:
        for tr in all_goalies[i].xpath("tbody/tr"):
            goalie = {}
            pid = tr.xpath("*[1]//a/@href")[0].split("/")[-1]  # Id
            goalie["name"] = tr.xpath(".//a")[0].text       # Nimi
            goalie["team"] = team                           # Joukkue (away/home)
            for j, td in enumerate(tr.xpath("td")[1:]):     # Tilastot
                col = goalie_cols[j].text_content().strip().lower()
                goalie[col] = parse_stat_value(td)
            goalies[pid] = goalie
        # Kenttäpelaajat:
        for tr in all_skaters[i].xpath("tbody/tr"):
            skater = {}
            pid = tr.xpath("*[1]//a/@href")[0].split("/")[-1]  # Id
            skater["name"] = tr.xpath(".//a")[0].text       # Nimi
            skater["team"] = team                           # Joukkue (away/home)
            for k, td in enumerate(tr.xpath("td")[1:]):     # Tilastot
                col = skater_cols[k].text_content().strip().lower()
                skater[col] = parse_stat_value(td)
            skaters[pid] = skater
        game["skaters"], game["goalies"] = skaters, goalies

    t1 = time.time() - t1
    log_done("scrape_game", t0, t1, gid)
    memcache.set(gid, game)
    return game


def scrape_schedule():
    """
    Skreippaa kauden tulevien pelien alkamisajat ja joukkueet.
    Huom! ei skreippaa jo pelattuja otteluita.

    Palauttaa dictionaryn, jossa avaimena joukkueen tunnus,
    arvoina dictionaryssä ottelun alkamisaika sekä joukkueet.
    """
    schedule = memcache.get("schedule")
    if schedule is not None:
        return schedule

    season = SEASON + str(int(SEASON) + 1)
    url = "http://nhl.com/ice/schedulebyseason.htm?season=" + season

    t0 = time.time()
    try:
        response = urlfetch.fetch(url)
        t0 = time.time() - t0
        if response.status_code != 200:
            return None
    except:
        return None

    t1 = time.time()
    root = html.fromstring(response.content)
    schedule = {team: [] for team in TEAMS}
    rows = root.xpath("//div[@class='contentBlock']/table[1]/tbody/tr")
    for row in rows:
        if row.xpath("td[4]/*"):
            date_str = row.xpath("td[1]/div[1]/text()")[0][4:]
            time_str = row.xpath("td[4]/div[1]/text()")[0].replace(" ET", "")
            datetime_str = str(str_to_date(date_str + " " + time_str))
            datetime_str = datetime_str.split("+")[0]
        else:
            # Joidenkin pelien alkamiskellonaika ei ole tiedossa (pvm on),
            # mitäköhän niille tekisi?
            datetime_str = ""
        home_city = row.xpath("td[2]")[0].text_content().lower()
        away_city = row.xpath("td[3]")[0].text_content().lower()
        home_team = TEAMS[CITIES.index(home_city)]
        away_team = TEAMS[CITIES.index(away_city)]
        game = {"time": datetime_str, "home": home_team, "away": away_team}
        schedule[home_team].append(game)
        schedule[away_team].append(game)

    t1 = time.time() - t1
    log_done("scrape_schedule", t0, t1)
    memcache.set("schedule", schedule, 60 * 60 * 12)
    return schedule


def scrape_standings(year="season_" + SEASON):
    """
    Skreippaa sarjataulukon.

    Palauttaa dictionaryn, jossa avaimena joukkueen tunnus, arvona
    joukkueen tilastot (gp,w,l,otl...), konferenssi sekä divisioona.
    """
    if not "season_" in year:
        year = "season_" + year
    standings = memcache.get("standings" + year)
    if standings is not None:
        return standings

    url = URL_YAHOO + "/standings?year=" + year
    t0 = time.time()
    try:
        response = urlfetch.fetch(url)
        t0 = time.time() - t0
        if response.status_code != 200:
            return None
    except:
        return None

    t1 = time.time()
    root = html.fromstring(response.content)
    table = root.xpath("//tr[count(td)=3]/td[1]/table[2]")[0]
    rows = table.xpath("tr[contains(@class, 'ysprow')]")
    columns = table.getchildren()[1].getchildren()[1:]
    standings = {}

    for i, row in enumerate(rows):
        team_stats = {}
        team_stats["div"] = DIVISIONS[i / 5]
        team_stats["conf"] = CONFERENCES[i / 15]
        tds = row.iterchildren()
        team = tds.next().xpath("a/@href")[0].split("/")[-1]
        for column in columns:
            col = column.text_content().strip().lower()
            team_stats[col] = parse_stat_value(tds.next())
        standings[team] = team_stats

    t1 = time.time() - t1
    log_done("scrape_standings", t0, t1, year)
    expires = 60 * 30 if year == SEASON else 0
    memcache.set("standings" + year, standings, expires)
    return standings


### APUFUNKTIOT ###


def get_next_games(team=None, pid=None):
    """
    Palauttaa listan, jossa joukkueen/pelaajan tulevien otteluiden
    alkamisaika, kotijoukkue ja vierasjoukkue.

    Lista on järjestetty alkamisajan mukaan siten, että seuraavan pelin saa
    helposti kutsumalla get_next_games(team="ana")[0].
    """
    if pid:
        try:
            team = scrape_players()[pid]["team"]
        except KeyError:
            return None
        key = pid
    elif team:
        if not team in TEAMS:
            return None
        key = team
    else:
        return None

    data = sorted(scrape_schedule()[team], key=lambda x: x["time"])
    return {key: data}


def get_latest_game(team=None, pid=None):
    """
    Palauttaa joukkueen/pelaajan viimeisimmän pelatun pelin id:n.
    """
    if team:
        games = scrape_games_by_team(team)
    elif pid:
        games = scrape_games_by_player(pid)
    if not games:
        return None
    return max(games)


def add_cache(key, value, check):
    """
    Lisää arvon välimuistiin, määrittää vanhenemisajan otteluohjelman
    mukaan.

    Välimuistiin tallennetaan skreipatun datan lisäksi tarkistusarvo (check),
    jolle (toisin kuin varsinaiselle datalle) ei aseteta ekspiraatioaikaa.
    Check-muuttujan perusteella arvioidaan, onko välimuistiin tallennettu
    tieto vanhentunutta. Tarkistusarvo voi olla esim. pelaajan uran aikana
    pelattujen pelien lukumäärä.
    Välimuistiin lisättäessä tarkistetaan, onko vanha tarkistusarvo eri kuin
    uusi tarkistusarvo (esimerkkitapauksessa onko pelaaja pelannut lisää
    otteluita sitten viime välimuistitallennuksen). Jos arvot eriävät,
    data tallennetaan välimuistiin ja ekspiraatioaika asetetaan siten, että
    data poistuu välimuistista juuri ennen pelaajan seuraavan ottelun
    päättymistä. Jos arvot ovat samat, data tallennetaan välimuistiin vain
    lyhyeksi ajaksi, koska voidaan olettaa, että skreipattavalle sivulle
    lisätään lähitulevaisuudessa uutta dataa.

    Tallennettava arvo on sellainen, joka päivittyy aina pelattujen
    pelien myötä, eli jokin seuraavista:
    - pelaajan kaudella x pelatut pelit  (avain: "games_5002012")
    - joukkueen kaudella x pelatut pelit (avain: "games_ana2012")
    - pelaajan kauden x tilastot         (avain: "stats_5002012")
    - pelaajan koko uran tilastot        (avain: "stats_500")
    - joukkueen kauden x tilastot        (avain: "stats_ana2012")
    """
    postfix = key.split("_")[1]
    if len(postfix) > 4:
        ident, year = postfix[:-4], postfix[-4:]
    else:
        ident, year = postfix, None

    # Edellisten kausien tiedot eivät vanhene:
    if year and year != SEASON:
        memcache.set(key, value)
        return

    # Muuten asetetaan vanhenemisaika seuraavan ottelun mukaan:
    old_check = memcache.get(key + "check")
    if old_check and old_check == check:
        # Tallennettava arvo on sama kuin viimeksi vanhentunut arvo,
        # (esim. pelattavan ottelun tiedot eivät ole vielä päivittyneet).
        # Asetetaan vanhenemisajaksi 10 minuuttia:
        memcache.set(key, value, 60 * 10)
    else:
        # Arvo on muuttunut, selvitetään seuraavan ottelun ajankohta:
        try:
            if ident.isalpha():
                next_game_time = get_next_games(team=ident)[team][0]["time"]
            else:
                next_game_time = get_next_games(pid=ident)[pid][0]["time"]
        # Jos seuraavaa ottelua ei löydy,
        # asetetaan seuraavan ottelun ajankohdaksi nyt + 1 päivä:  TODO
        except Exception as e:
            logging.error("Seuraavaa ottelua ei löydetty. " + str(e))
            dt = datetime.now() + timedelta(days=1)
            next_game_time = str(dt)[:19]

        # Välimuistin arvo vanhenee 2 tuntia pelin alkamisen jälkeen:
        game_end_time = isostr_to_date(next_game_time) + timedelta(
            hours=2)
        time_diff = (game_end_time - datetime.utcnow()).total_seconds()
        memcache.set(key, value, time_diff)
        memcache.set(key + "check", check)
        logging.info("""add_cache(%s)
                     Vanhenemisaika %.1fmin""" % (key, time_diff / 60.0))


def parse_stat_value(value):
    """
    Ottaa tilastoarvon sisältävän elementti-olion, palauttaa tilastoarvon
    merkkijonona, tyhjiöarvona, kokonais-tai liukulukuna.
    """
    value_str = value.text_content().strip().lower()
    if not value_str:
        return None
    if value_str == "-":
        return 0.0  # FO%-sarakkeeseen voi olla merkitty pelkkä viiva
    if value_str.isdigit() or value_str[0] in ["-", "+"]:
        return int(value_str)
    if value_str.startswith("."):
        return float(value_str)
    if value_str == "n/a":
        return None
    if value_str in ALT_TEAMS:
        value_str = ALT_TEAMS[value_str]
    return value_str


def toi_to_sec(toi):
    """
    Peliaika sekunneiksi.

    >>> toi_to_sec("22:18")
    1338
    """
    splits = toi.split(":")
    return int(splits[0]) * 60 + int(splits[1])


def sec_to_toi(sec):
    """
    Sekunnit peliajaksi.

    >>> print sec_to_toi("1234")
    20:34
    """
    sec = int(sec)
    return "%d:%d" % (sec / 60, sec % 60)


def str_to_date(datetime_str):
    """
    Ottaa merkkijonon muotoa "FEB 6, 2013 7:30 PM", palauttaa
    datetime-objektin.

    Parametrin aikavyöhyke on EST, paluuarvon GMT+-0.

    >>> dt = str(str_to_date("FEB 6, 2013 7:30 PM")).split("+")[0]
    >>> dt in ["2013-02-07 01:30:00", "2013-02-07 00:30:00"]
    True
    """
    format = "%b %d, %Y %I:%M %p"
    eastern, gmt = timezone("US/Eastern"), timezone("GMT")
    dt = datetime.strptime(datetime_str, format)
    dt_eastern = eastern.localize(dt)
    dt_gmt = dt_eastern.astimezone(gmt)
    return dt_gmt


def isostr_to_date(datetime_str):
    """
    Ottaa ISO-formatoidun merkkijonon, palauttaa datetime-objektin.

    >>> print isostr_to_date("2013-02-28 16:12:00")
    2013-02-28 16:12:00
    """
    format = "%Y-%m-%d %H:%M:%S"
    return datetime.strptime(datetime_str, format)


def test():
    """Muutama testi debuggausta varten."""
    players = scrape_players("jarome iginla")
    assert len(players) == 1
    pid = players.keys()[0]
    assert pid == "1453"
    assert scrape_career(pid)["2000"]["ppg"] == 10
    assert scrape_games_by_player(pid, "2012")["2013021503"]["opponent"] == "stl"
    games = scrape_games_by_team("ana", "2011")
    game = games[sorted(games.keys())[0]]
    assert game["opponent"].lower().startswith("phoenix")
    gid1 = sorted(games.keys())[0]
    assert gid1 == "2011092025"
    gid2 = "2013042522"
    g1, g2 = scrape_game(gid1), scrape_game(gid2)
    assert g1["skaters"]["500"]["shifts"] == 23
    assert g1["goals"][-1]["desc"].startswith("Petteri")
    assert g2["skaters"]["5346"]["take"] == 0
    standings = scrape_standings("2011")
    assert standings["nyr"]["w"] == 51
    assert standings["tam"]["home"] == "25-14-2"
    assert standings["ana"]["conf"] == "west"
    assert standings["det"]["div"] == "central"
    print "Tests OK"
