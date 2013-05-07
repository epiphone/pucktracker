# -*- coding: utf-8 -*-
"""
URL-reititykset ja sivut OAuth-toimintoja lukuunottamatta.

|           URL           |    Funktio    |            Kuvaus            |
|-------------------------|---------------|------------------------------|
| /                       | index         | Käyttäjäkohtainen index-sivu |
| /menu                   | menu          | Main Menu                    |
| /player                 | player_search | Pelaajahaku                  |
| /player/<player_id>     | player        | Pelaaja-sivu                 |
| /team                   | team_search   | Joukkuehaku                  |
| /team/<team>            | team          | Joukkue-sivu                 |
| /game/<game_id>         | game          | Ottelusivu                   |
| /standings/<int:year>   | standings     | Sarjataulukko                |
| /top                    | search        | TODO: Top-sivu               |

"""

import logging
from application import app
from flask import render_template, session,  request, abort
from utils import fetch_from_api, logged_in, get_latest_game
from utils import get_followed
from jinja_utils import convert_date
import urllib


# Kaikki joukkueet tunnuksineen ja nimineen
TEAMS = {"bos": "Boston Bruins", "san": "San Jose Sharks", "nas": "Nashville Predators", "buf": "Buffalo Sabres", "cob": "Columbus Blue Jackets", "wpg": "Winnipeg Jets","cgy": "Calgary Flames", "chi": "Chicago Blackhawks", "det": "Detroit Red Wings", "edm": "Edmonton Oilers", "car": "Carolina Hurricanes", "los": "Los Angeles Kings", "mon": "Montreal Canadiens", "dal": "Dallas Stars", "njd": "New Jersey Devils", "nyi": "New York Islanders", "nyr": "New York Rangers", "phi": "Philadelphia Flyers", "pit": "Pittsburgh Penguins", "col": "Colorado Avalanche", "stl": "St. Louis Blues", "tor": "Toronto Maple Leafs", "van": "Vancouver Canucks", "was": "Washington Capitals", "pho": "Phoenix Coyotes", "ott": "Ottawa Senators", "tam": "Tampa Bay Lightning", "ana": "Anaheim Ducks", "fla": "Florida Panthers", "min": "Minnesota Wild"}
# Ottelusivun mahdolliset pelaajatilastosarakkeet oikeassa järjestyksessä:
SKATER_COLS = ["name", "G", "A", "+/-", "SOG", "PIM", "S", "BS", "Hits",
               "Take", "Give", "FW", "FL", "FO%", "Shifts", "TOI"]
GOALIE_COLS = ["name", "SA", "Shots", "GA", "SV", "Saves", "SV%", "PIM", "TOI"]


@app.route("/")
def index():
    """
    Kirjautuneelle käyttäjälle näytetään "oma sivu", jossa seurattujen
    pelaajien/joukkueiden kauden tilastot sekä uusimpien otteluiden tiedot.

    Kirjautumatonta käyttäjää kehotetaan kirjautumaan sisään.
    """
    if logged_in():
        user_data = get_followed(ids_only=False)
        if not user_data:
            # TODO tähän parempi virheenkäsittely
            return render_template(
                "error.html", e="Jotain mystista tapahtui..")

        # Joukkueet viimeisimmän ottelun mukaan järjestettyyn listaan
        # Lista sisältää vain templatelle olennaisen datan
        teams = []
        for k, v in user_data['teams'].iteritems():
            new_team = {
                'id': k,
                'stats': v['stats'],
                'latest_game': get_latest_game(v['games'])}
            teams.append(new_team)
        teams.sort(key=lambda v: v['latest_game']['date'], reverse=True)

        # Samoin pelaajat
        players = []
        for k, v in user_data['players'].iteritems():
            stats = v['stats'] or None
            if v['games']:
                latest_game = get_latest_game(v['games'])
            else:
                latest_game = None

            new_player = {
                'id': k,
                'stats': stats,
                'latest_game': latest_game}
            players.append(new_player)
        players.sort(key=lambda v: v['latest_game']['date'], reverse=True)

        return render_template("index.html", teams=teams, players=players)
    else:
        return render_template("login.html")


@app.route("/menu")
def menu():
    """
    Main Menu.

    Navigointilinkit eri sivuille.
    """
    return render_template("menu.html")


@app.route("/player")
def player_search():
    '''
    Pelaajahaku.

    Jos hakuehtoa ei ole määritelty, esim. "/player?q=teemu", näytetään pelkkä
    hakukenttä. Muuten näytetään hakukentän alla API:n palauttama lista
    hakuehtoa vastaavista pelaajista.
    '''
    query = request.args.get('q')
    if query:
        logging.info("*****" + str(query))
        logging.info("Haetaan pelaajia hakuehdolla: %s" % query)
        players = fetch_from_api("/api/json/players?query=%s" % query)
        return render_template(
            "player_search.html", players=players, query=query)
    else:
        return render_template("player_search.html")


@app.route("/player/<player_id>")
def player(player_id):
    '''
    Yksittäisen pelaajan tiedot.

    Käyttäjä voi lisätä/poistaa pelaajan seurattavien pelaajien listasta.
    '''
    all_players = fetch_from_api("/api/json/players")
    if not player_id in all_players:
        abort(400)

    all_seasons = fetch_from_api("/api/json/players/%s" % player_id)
    if not all_seasons:
        # TODO all_seasons voi olla None tai tyhjä tietorakenne;
        # jälkimmäisessä tapauksessa pelaaja ei ole pelannut yhtään ottelua,
        # tulee käsitellä!
        abort(400)
    season_games = fetch_from_api(
        "/api/json/games?pid=%s&year=2012" % player_id)

    name = all_players[str(player_id)]['name']
    position = all_players[str(player_id)]['pos'].lower()
    team = all_players[str(player_id)]['team']

    this_season = all_seasons['2012']
    career = all_seasons['career']
    del all_seasons['career']

    # Poistetaan pelaaja-lista-dictionary -rakenteesta yksi dictionary-taso,
    # jotta Jinja template-engine osaa loopata tietorakenteen läpi ilman ongelmaa.
    career_list = []
    for k, v in all_seasons.iteritems():
        new_dict = v
        new_dict['year'] = k
        career_list.append(new_dict)

    # Järjestetään pelaajalista
    career_list = sorted(career_list, key=lambda x: x["year"], reverse=False)

    return render_template(
        "player.html",
        name=name,
        team=team,
        this_season=this_season,
        all_seasons=career_list,
        position=position,
        career=career,
        games=season_games,
        pid=player_id)


@app.route("/team")
def team_search():
    '''
    Joukkuehaku.

    Kaikki joukkueet listattuna ja suodatettavissa hakuehdolla.
    '''
    return render_template("team_search.html", teams=TEAMS)


@app.route("/team/<team>")
def team(team):
    """
    Yksittäisen joukkueen tiedot.
    """
    logging.info("Haetaan joukkueen %s tiedot" % team)
    stats = fetch_from_api("/api/json/teams?team=%s" % team)
    if not stats:
        abort(400)
    games = fetch_from_api("/api/json/games?team=" + team)

    #Haetaan joukkueen pelaajat:
    all_skaters = fetch_from_api("/api/json/top?goalies=0&limit=1000")
    all_goalies = fetch_from_api("/api/json/top?goalies=1&limit=1000")
    team_skaters = [skater for skater in all_skaters if skater["team"] == team]
    team_goalies = [goalie for goalie in all_goalies if goalie["team"] == team]

    return render_template(
        "team.html",
        team=team,
        stats=stats,
        skaters=team_skaters,
        goalies=team_goalies,
        games=games)


@app.route("/game/<game_id>")
def game(game_id):
    '''
    Yksittäisen ottelun tiedot.
    '''
    logging.info("Haetaan pelin %s tiedot" % game_id)
    game = fetch_from_api("/api/json/games/%s" % game_id)
    if not game:
        abort(400)

    # Lisätään dictionaryyn eräkohtaisesti listat maaleista:
    goals_dict = {i: [] for i in range(1, 5)}
    for goal in game["goals"]:
        period = goal["period"]
        goals_dict[period].append(goal)

    # Lajitellaan pelaajat joukkueittain listoihin:
    players = dict(home_skaters=[], away_skaters=[], home_goalies=[],
        away_goalies=[])
    for position in ["skaters", "goalies"]:
        for k, v in game[position].iteritems():
            v["pid"] = k
            key = v["team"] + "_" + position
            players[key].append(v)

    # Järjestetään pelaajalistat sukunimen perusteella:
    sort_func = lambda x: x["name"].split()[-1]
    for k, v in players.iteritems():
        players[k] = sorted(v, key=sort_func)

    # Selvitetään pelaajatilastojen sarakkeet (voivat vaihdella):
    skater_cols = game["skaters"].values()[0].keys()
    goalie_cols = game["goalies"].values()[0].keys()
    sorted_skater_cols, sorted_goalie_cols = [], []
    for col in SKATER_COLS:
        if col.lower() in skater_cols:
            sorted_skater_cols.append(col)
    for col in GOALIE_COLS:
        if col.lower() in goalie_cols:
            sorted_goalie_cols.append(col)

    return render_template(
        "game.html",
        gid=game_id,
        game=game,
        goals=goals_dict,
        players=players,
        skater_cols=sorted_skater_cols,
        goalie_cols=sorted_goalie_cols)


@app.route("/standings/<int:year>")
def standings(year):
    """
    Sarjataulukko joka sisältää kaikkien joukkueiden nykyisen kauden tilastot.

    Järjestetty pisteiden mukaan, divisioonittain.
    """
    stats = fetch_from_api("/api/json/teams?&year=%s" % year)
    if not stats:
        abort(400)

    teams_dict = {}  # Dict, jossa avaimena on divisioona ja arvona joukkue
    teams = sorted(  # Järjestetään joukkueet listaan pts:n mukaan
        stats.iteritems(),
        key=lambda (k, v): v["pts"],
        reverse=True)

    # Järjestetään joukkueet divisioonittain
    for k, v in teams:
        div = v["div"]
        v["team"] = k
        if not div in teams_dict:
            teams_dict[div] = [v]
        else:
            teams_dict[div].append(v)

    return render_template("standings.html", teams=teams_dict, year=str(year))


@app.route("/top")
def top():
    """
    Kauden parhaiden pelaajien lista.

    Url-parametrit:
        year: määrittää kauden, oletuksena nykyinen kausi.
        sort: määrittää järjestyksen, vaihtoehdot ovat
          - pelaajilla name, team, gp, g, a, pts, +/-, pim, hits, bks, fw, fl,
                       fo%, ppg, ppa, shg, sha, gw, sog, pct (oletuksena pts)
          - maalivahdeilla name, team, gp, gs, min, w, l, otl, ega, ga, gaa,
                           sa, sv, sv%, so (oletuksena w)
        goalies: (0 tai 1) määrittää haetaanko maalivahteja, oletuksena ei.
        playoffs: (0 tai 1) playoffit vai runkosarja, oletuksena runkosarja.
        reverse: (0 tai 1) määrittää järjestyksen suunnan,
                           oletuksena reverse=1, eli suurin arvo ensin.
        limit: määrittää tulosten maksimimäärän, oletuksena 30.
    """
    year = request.args.get("year", "2012")
    goalies = request.args.get("goalies", "0")
    playoffs = request.args.get("playoffs", "0")
    reverse = request.args.get("reverse", "1")
    limit = request.args.get("limit", "30")
    default_sort = "w" if goalies == "1" else "pts"
    sort = request.args.get("sort", default_sort)
    goalie_sorts = ["gs", "min", "w", "l", "otl", "ega", "ga", "gaa", "sa",
        "sv", "sv%", "so"]

    if goalies == "1":
        if sort not in ["name", "team", "gp"] + goalie_sorts:
            sort = "w"
    elif sort in goalie_sorts:
        sort = "pts"

    params = dict(year=year, sort=sort, goalies=goalies, playoffs=playoffs,
        reverse=reverse, limit=limit)

    players = fetch_from_api("/api/json/top?" + urllib.urlencode(params))
    if not players:
        abort(400)

    return render_template(
        "top.html",
        players=players,
        year=year,
        playoffs=playoffs,
        goalies=goalies,
        reverse=reverse,
        sort=sort,
        limit=limit)


### Error handlers ###
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', e=e), 404


@app.errorhandler(400)
def bad_request(e):
    return render_template('error.html', e=e), 400
