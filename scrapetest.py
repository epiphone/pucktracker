# -*-coding:utf-8-*-
# Screippaustesti


from lxml import html
import time
import datetime as dt
import logging
from google.appengine.api import urlfetch, memcache

MONTHS = ["", "jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]
TEAMS = ["njd", "nyi", "nyr", "phi", "pit", "bos", "buf", "mon", "ott", "tor",
         "car", "fla", "tam", "was", "wpg", "chi", "cob", "det", "nas", "stl",
         "cgy", "col", "edm", "min", "van", "ana", "dal", "los", "pho", "san"]
CITIES = ["new jersey", "ny islanders", "ny rangers", "philadelphia",
          "pittsburgh", "boston", "buffalo", u"montréal", "ottawa", "toronto",
          "carolina", "florida", "tampa bay", "washington", "winnipeg",
          "chicago", "columbus", "detroit", "nashville", "st. louis",
          "calgary", "colorado", "edmonton", "minnesota", "vancouver",
          "anaheim", "dallas", "los angeles", "phoenix", "san jose"]

# Eri sivuilta poimitaan erilaisia tilastoja:
GAME_LOG_COLUMNS = ["opponent", "result", "g", "a", "pts", "+/-", "pim",
                    "ppg", "hits", "bks", "ppa", "shg", "sha", "gw", ",gt",
                    "sog", "pct"]
BOXSCORE_COLUMNS_GOALIE = ["sa", "ga", "sv", "sv%", "pim", "toi"]
BOXSCORE_COLUMNS = ["g", "a", "pts", "+/-", "pim", "s", "bs", "hits", "fw",
                    "fl", "fo%", "shifts", "toi"]


def scrape_ids():
    """Palauttaa dictionaryn jossa avaimena pelaajan nimi, arvona
    joukkue, id ja koko kauden tilastot."""
    url = "http://sports.yahoo.com/nhl/stats/byposition?pos="
    all_ids = {}
    for param in ["C,RW,LW,D", "G"]:
        url0 = url + param
        t0 = time.time()
        page = urlfetch.fetch(url)
        root = html.fromstring(page.content)
        t1 = time.time() - t0
        logging.info(
            "Haettiin html ja muokattiin lxml-objektiksi ajassa " + str(t1))

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
                text = td.text_content().strip().lower()
                if text != "":
                    stats[columns[i]] = text
                    i += 1
            ids[name] = stats
        all_ids = dict(all_ids.items() + ids.items())

    t1 = time.time() - t0
    logging.info("Objektista parsettiin data ajassa" + str(t1))
    return all_ids


def scrape_player_games(pid, year="2012"):
    """Palauttaa pelaajan pelatut pelit. Paluuarvona dictionary, jonka avaimena
    ottelun id, arvona pelaajan tilastot kyseisestä pelistä."""
    games = memcache.get(pid + year)
    if games:
        logging.info("scrape_player_games(%s, %s) - Loytyi valimuistista."
            % (pid, year))
        return games
    logging.info("scrape_player_games(%s, %s) - Ei loytynyt valimuistista."
            % (pid, year))
    url = "http://sports.yahoo.com/nhl/players/%s/gamelog?year=%s" % (pid, year)
    t0 = time.time()
    response = urlfetch.fetch(url)
    t0 = time.time() - t0
    if response.status_code != 200:
        raise web.notfound()

    t1 = time.time()
    root = html.fromstring(response.content)
    games = {}
    rows = root.xpath("//table/tr[@class='ysprow1' or @class='ysprow2' and position() < last()]")
    for row in rows:
        game = {}
        gid = row.xpath("td/a/@href")[0].split("gid=")[-1]
        for i, td in enumerate(row.xpath("td")[1:-1]):
            game[GAME_LOG_COLUMNS[i]] = td.text_content().strip()
        games[gid] = game  # games == {"123":{"opponent":"asd","g":4,...}, "124":{...}, ...}

    t1 = time.time() - t1
    logging.info("""scrape_player_games(%s, %s):
                 Haettiin HTML ajassa %s
                 Skreipattiin data ajassa %s"""
                 % (pid, year, str(t0), str(t1)))
    memcache.add(pid + year, games, 60 * 60)
    return games


def scrape_team_games(team, year="2012"):
    """Palauttaa dictionaryn jossa avaimena joukkueen PELATTUJEN otteluiden
    id:t, arvona ottelun 'nimi' (esim. 'Boston Bruins vs Boston (0-1-2)')."""
    team = team.lower()
    if not team in TEAMS:
        # raise Exception("Virheellinen joukkueen nimi.")
        raise web.notfound()

    url = ("http://sports.yahoo.com/nhl/teams/%s/schedule?"
           "view=print_list&season=%s") % (team, year)
    t0 = time.time()
    response = urlfetch.fetch(url)
    t0 = time.time() - t0
    if response.status_code != 200:
        raise web.notfound()

    t1 = time.time()
    root = html.fromstring(response.content)
    rows = root.xpath("//tbody/tr[td[3]/a[contains(@href, 'recap')]]")
    games = {}
    for row in rows:
        href = row.xpath("td[3]/a/@href")[0]
        gid = href.split("gid=")[-1]  # TODO entä jos gid:n jälkeen toinen parametri?
        games[gid] = row.xpath("td")[1].text_content().strip()

    t1 = time.time() - t1
    logging.info("""scrape_team_games(%s, %s):
                 Haettiin HTML ajassa %s
                 Skreipattiin data ajassa %s"""
                 % (team, year, str(t0), str(t1)))
    return games


def scrape_game(gid):
    """Palauttaa dictionaryn, jossa hirveä läjä dataa ottelusta."""
    t0 = time.time()
    url = "http://sports.yahoo.com/nhl/boxscore?gid=" + gid
    response = urlfetch.fetch(url)
    t0 = time.time() - t0
    if response.status_code != 200:
        raise web.notfound()

    t1 = time.time()
    root = html.fromstring(response.content)
    game = {}
    # Ottelun tulos:
    game["away_team"] = root.xpath("//div[@class='away']//a")[0].attrib["href"].split("/")[-1]
    game["home_team"] = root.xpath("//div[@class='home']//a")[0].attrib["href"].split("/")[-1]
    game["away_score"] = root.xpath("//div[@class='away']/*")[0].text_content().strip()
    game["home_score"] = root.xpath("//div[@class='home']/*")[0].text_content().strip()

    # Maalit ja mahd. shootout:
    periods = root.xpath("(//div[count(h5)>2])[1]/table")
    goals, shootout = [], []
    for i, period in enumerate(periods[:3]):  # Varsinaisen peliajan maalit
        for tr in period.xpath("tbody/tr[count(td)>3]"):
            tds = tr.xpath("td")
            goal = {}
            goal["period"] = i + 1
            goal["time"] = tds[0].text_content().strip()
            goal["team"] = tds[1].xpath("a/@href")[0].split("/")[-1]
            goal["desc"] = tds[2].text_content().strip()
            goal["score"] = tds[3].text_content().strip()
            goals.append(goal)
    if len(periods) > 3:
        if len(periods[3].xpath("tbody/tr[count(td)>3]")) != 0:  # Jatkoaika
            goal = {}
            goal["period"] = 4
            goal["time"] = tds[0].text_content().strip()
            goal["team"] = tds[1].xpath("a/@href")[0].split("/")[-1]
            goal["desc"] = tds[2].text_content().strip()
            goal["score"] = tds[3].text_content().strip()
            goals.append(goal)
        else:  # Shootout
            for tr in periods[4].xpath("tbody/tr"):
                attempt = {}
                attempt["team"] = tr.xpath("td/a/@href")[0].split("/")[-1]
                attempt["desc"] = tr.xpath("td[last()]")[0].text_content().strip()
                shootout.append(attempt)
    game["goals"], game["shootout"] = goals, shootout

    # Pelaajakohtaiset tilastot:
    all_goalies = root.xpath("//div[contains(@class, 'goalies')]/table")
    all_skaters = root.xpath("//div[contains(@class, 'skaters')]/table")
    for i, team in enumerate(["away", "home"]):
        team_goalies = {}
        # Maalivahdit:
        for tr in all_goalies[i].xpath("tbody/tr"):
            goalie = {}
            pid = tr.xpath(".//a/@href")[0].split("/")[-1]  # Id
            goalie["name"] = tr.xpath(".//a")[0].text       # Nimi
            for j, td in enumerate(tr.xpath("td")[1:]):     # Tilastot
                goalie[BOXSCORE_COLUMNS_GOALIE[j]] = td.text_content().strip()
            team_goalies[pid] = goalie
        # Loput:
        team_skaters = {}
        for tr in all_skaters[i].xpath("tbody/tr"):
            skater = {}
            pid = tr.xpath(".//a/@href")[0].split("/")[-1]  # Id
            skater["name"] = tr.xpath(".//a")[0].text       # Nimi
            for k, td in enumerate(tr.xpath("td")[1:]):     # Tilastot
                skater[BOXSCORE_COLUMNS[k]] = td.text_content().strip()
            team_skaters[pid] = skater
        game[team] = dict(goalies=team_goalies, skaters=team_skaters)

    t1 = time.time() - t1
    logging.info("""scrape_game(%s):
                 Haettiin HTML ajassa %s
                 Skreipattiin data ajassa %s""" % (gid, str(t0), str(t1)))
    return game


def scrape_schedule(season="20122013", playoffs=False):
    """Skreippaa kauden tulevien pelien alkamisajat ja joukkueet.

    Paluuarvo on muotoa
    {"ana": [
        {"time": "2012-02-06 21:30:00", "home":"ana", "away":"bos"},
        {"time": "2012-02-07 16:00:00", "home":"cal", "away":"ana"},
        ...],
     "bos": [
        {"time": "2012-02-06 21:30:00", "home:"ana", "away":"bos"},
        ...],
     ...}
    """
    t0 = time.time()
    url = "http://nhl.com/ice/schedulebyseason.htm?season=%s"
    if playoffs:
        url += "&gameType=3"
    page = urlfetch.fetch(url)
    root = html.fromstring(page.content)
    logging.info("Haettiin html ja luotiin lxml-objekti ajassa " +
                 str(time.time() - t0))

    t0 = time.time()
    schedule = {team: [] for team in TEAMS}
    rows = root.xpath("//div[@class='contentBlock']/table[1]/tbody/tr")
    for row in rows:
        if row.xpath("td[4]/*"):
            date_str = row.xpath("td[1]/div[1]/text()")[0][4:]
            time_str = row.xpath("td[4]/div[1]/text()")[0].replace(" ET", "")
            datetime_str = str(str_to_date(date_str + " " + time_str))
        else:
            # Joidenkin pelien alkamisaika ei ole tiedossa (pvm on), mitäköhän
            # niille tekisi?
            datetime_str = ""
        home_city = row.xpath("td[2]")[0].text_content().lower()
        away_city = row.xpath("td[3]")[0].text_content().lower()
        home_team = TEAMS[CITIES.index(home_city)]
        away_team = TEAMS[CITIES.index(away_city)]
        game = {"time": datetime_str, "home": home_team, "away": away_team}
        schedule[home_team].append(game)
        schedule[away_team].append(game)

    logging.info("Skreipattiin data ajassa " + str(time.time() - t0))
    CACHE_SCHEDULE = schedule
    return schedule


def get_next_game(team=None, pid=None):
    """Palauttaa dictionaryn, jossa joukkueen/pelaajan seuraavan pelin
    alkamisaika, kotijoukkue ja vierasjoukkue. Esim:
    {"time": "2013-02-28 10:30:00", "home":"ana", "away":"bos"}}
    """
    if team:
        return sorted(scrape_schedule()[team], key=lambda x: x["time"])[0]
    return "kesken"


def get_latest_game(team=None, pid=None):
    """Palauttaa joukkueen/pelaajan viimeisimmän pelatun pelin id:n."""
    if team:
        return sorted(scrape_team_games(team))[-1]
    return sorted(scrape_player_games(pid))[-1]


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


def test():
    """Testejä ja käyttöesimerkkejä."""
    assert get_pid("teemu selanne") == "500"
    assert scrape_ids()["teemu selanne"]["team"] == "ana"
    assert not "g" in scrape_ids()["tuukka rask"]  # Maalivahdilla ei maaleja.

    gid = get_latest_game("pit")
    game = scrape_game(gid)
    if game["home_team"] == "pit":
        opponent = game["away_team"]
    else:
        opponent = game["home_team"]
    assert get_latest_game(opponent) == gid


def get_average_toi(pid):
    """Lasketaan pelaajan peliajan keskiarvo."""
    games = scrape_player_games(pid)
    total_toi = 0
    for gid in games:
        print "Skreipataan ottelu", gid
        data = scrape_game(gid)
        if games[gid]["opponent"].startswith("@"):
            team = "away"
        else:
            team = "home"
        player = "skaters" if pid in data[team]["skaters"] else "goalies"
        total_toi += toi_to_sec(data[team][player][pid]["toi"])  # Maalivahdit?
    return total_toi / len(games)


def toi_to_sec(toi):
    """Peliaka sekunteiksi.

    >>> toi_to_sec("22:18")
    1338
    """
    splits = toi.split(":")
    return int(splits[0]) * 60 + int(splits[1])


def sec_to_toi(sec):
    """Sekunnit peliajaksi.

    >>> print sec_to_toi("1234")
    20:34
    """
    sec = int(sec)
    return "%d:%d" % (sec / 60, sec % 60)


def str_to_date(datetime_str, zone=-5):
    """Ottaa merkkijonon muotoa "FEB 6, 2013 7:30 PM", palauttaa
    datetime-objektin. Zone-parametri määrittää merkkijonon aikavyöhykkeen;
    Jos zone on -5, paluuarvoon lisätään 5 tuntia jolloin paluuarvon aika-
    vyöhyke on GMT+-0.

    >>> print str_to_date("FEB 6, 2013 7:30 PM", zone=-1)
    2013-02-06 20:30:00
    >>> print str_to_date("FEB 28, 2013 12:00 AM", zone=0)
    2013-02-28 00:00:00
    """
    format = "%b %d, %Y %I:%M %p"
    return dt.datetime.strptime(datetime_str, format) - dt.timedelta(hours=zone)


def isostr_to_date(datetime_str):
    """Ottaa ISO-formatoidun merkkijonon, palauttaa datetime-objektin.

    >>> print isostr_to_date("2013-02-28 16:12:00")
    2013-02-28 16:12:00
    """
    format = "%Y-%m-%d %H:%M:%S"
    return dt.datetime.strptime(datetime_str, format)
