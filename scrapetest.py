# -*-coding:utf-8-*-
# Screippaustesti


import lxml.html as html
import time

TEAMS = ["njd", "nyi", "nyr", "phi", "pit", "bos", "buf", "mon", "ott", "tor",
         "car", "fla", "tam", "was", "wpg", "chi", "cob", "det", "nas", "stl",
         "cgy", "col", "edm", "min", "van", "ana", "dal", "los", "pho", "san"]
# Game Log-sivujen skreipattavat tilastot:
GAME_LOG_COLUMNS = ["opponent", "result", "g", "a", "pts", "+/-", "pim",
                    "ppg", "hits", "bks", "ppa", "shg", "sha", "gw", ",gt",
                    "sog", "pct"]
CACHE_IDS = {}
CACHE_GAMES = {}
CACHE_TEAM_GAMES = {}
CACHE_PLAYER_GAMES = {}


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
            text = td.text_content().strip().lower()
            if text != "":
                stats[columns[i]] = text
                i += 1
        ids[name] = stats

    t1 = time.time() - t0
    print "Objektista parsettiin data ajassa", t1

    CACHE_IDS = ids
    return ids


def scrape_player_games(pid, season="2013"):
    """Palauttaa dictionaryn jossa avaimena joukkueen PELATTUJEN otteluiden
    id:t, arvona ottelun 'nimi' (esim. Boston Bruins vs Winnipeg Jets)."""
    pid = str(pid)
    try:
        return CACHE_PLAYER_GAMES[pid]
    except KeyError:
        print "Pelaajan otteluita ei löytynyt välimuistista, skreipataan..."

    url = "http://sports.yahoo.com/nhl/players/%s/gamelog" % pid
    t0 = time.time()
    root = html.parse(url)
    print "Haettiin HTML ja luotiin lxml-objekti ajassa", time.time() - t0

    t0 = time.time()
    games = {}
    for tr in root.xpath("//table/tr[@class='ysprow1' or @class='ysprow2']")[:-1]:
        game = {}
        gid = tr.xpath("td/a/@href")[0].split("gid=")[-1]
        for i, td in enumerate(tr.xpath("td")[1:-1]):
            game[GAME_LOG_COLUMNS[i]] = td.text_content().strip()
        games[gid] = game  # games == {"123":{"opponent":"asd","g":4,...}, "124":{...}, ...}

    print "Skreipattiin data ajassa", time.time() - t0
    CACHE_PLAYER_GAMES[pid] = games
    return games


def scrape_team_games(team, season="2013"):
    """Palauttaa dictionaryn jossa avaimena joukkueen PELATTUJEN otteluiden
    id:t, arvona ottelun 'nimi' (esim. Boston Bruins vs Winnipeg Jets)."""
    team = team.lower()
    if not team in TEAMS:
        raise Exception("Virheellinen joukkueen nimi.")

    # Jos ottelut löytyvät välimuistista, palautetaan ne:
    try:
        return CACHE_TEAM_GAMES[team]
    except KeyError:
        print "Joukkueen otteluita ei löytynyt välimuistista, skreipataan..."

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
    CACHE_TEAM_GAMES[team] = games
    return games


def scrape_game(gid):
    """Palauttaa dictionaryn, jossa hirveä läjä dataa ottelusta."""
    try:
        return CACHE_GAMES[gid]
    except KeyError:
        print "Ottelua ei löytynyt välimuistista, skreipataan..."
    t0 = time.time()
    url = "http://sports.yahoo.com/nhl/boxscore?gid=" + gid
    try:
        root = html.parse(url)
    except IOError:  # 404
        return None
    print "Haettiin HTML ja luotiin lxml-objekti ajassa", time.time() - t0

    t0 = time.time()
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
            for tr in period[4].xpath("tbody/tr"):
                attempt = {}
                attempt["team"] = tr.xpath("td/a/@href")[0].split("/")[-1]
                attempt["desc"] = tr.xpath("td[last()]")[0].text_content().strip()
                shootout.append(attempt)
    game["goals"], game["shootout"] = goals, shootout

    # Pelaajakohtaiset tilastot:
    all_goalies = root.xpath("//div[contains(@class, 'goalies')]/table")
    all_skaters = root.xpath("//div[contains(@class, 'skaters')]/table")
    for i, team in enumerate(["away", "home"]):
        team_goalies = []
        # Maalivahdit:
        for tr in all_goalies[i].xpath("tbody/tr"):
            goalie = []
            goalie.append(tr.xpath(".//a/@href")[0].split("/")[-1])  # Id
            goalie.append(tr.xpath(".//a")[0].text)  # Nimi
            [goalie.append(td.text_content().strip()) for td in tr.xpath("td")[1:]]  # Tilastot
            team_goalies.append(goalie)
        # Loput:
        team_skaters = []
        for tr in all_skaters[i].xpath("tbody/tr"):
            skater = []
            skater.append(tr.xpath(".//a/@href")[0].split("/")[-1])  # Id
            skater.append(tr.xpath(".//a")[0].text)  # Nimi
            [skater.append(td.text_content().strip()) for td in tr.xpath("td")[1:]]  # Tilastot
            team_skaters.append(skater)
        game[team] = dict(goalies=team_goalies, skaters=team_skaters)

    print "Skreipattiin data ajassa", time.time() - t0
    CACHE_GAMES[gid] = game
    return game


def get_latest_game(team):
    """Palauttaa joukkueen viimeisimmän pelatun pelin id:n."""
    return sorted(scrape_team_games(team))[-1]


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

    gid = get_latest_game("pit")
    game = scrape_game(gid)
    if game["home_team"] == "pit":
        opponent = game["away_team"]
    else:
        opponent = game["home_team"]
    assert get_latest_game(opponent) == gid
