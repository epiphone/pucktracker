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
| /game/<game_id>         | game          | Peli-sivu                    |
| /standings/<int:year>   | standings     | Sarjataulukko                |
| /top                    | search        | TODO: Top-sivu               |

"""

import logging
from application import app
from flask import render_template, session,  request, abort
from utils import fetch_from_api, get_latest_game, logged_in
from utils import get_followed
import json


# Kaikki joukkueet tunnuksineen ja nimineen
TEAMS = {"bos": "Boston Bruins", "san": "San Jose Sharks", "nas": "Nashville Predators", "buf": "Buffalo Sabres", "cob": "Columbus Blue Jackets", "wpg": "Winnipeg Jets","cgy": "Calgary Flames", "chi": "Chicago Blackhawks", "det": "Detroit Redwings", "edm": "Edmonton Oilers", "car": "Carolina Hurricanes", "los": "Los Angeles Kings", "mon": "Montreal Canadiens", "dal": "Dallas Stars", "njd": "New Jersey Devils", "nyi": "NY Islanders", "nyr": "NY Rangers", "phi": "Philadelphia Flyers", "pit": "Pittsburgh Penguins", "col": "Colorado Avalanche", "stl": "St. Louis Blues", "tor": "Toronto Maple Leafs", "van": "Vancouver Canucks", "was": "Washington Capitals", "pho": "Phoenix Coyotes", "sjs": "San Jose Sharks", "ott": "Ottawa Senators", "tam": "Tampa Bay Lightning", "ana": "Anaheim Ducks", "fla": "Florida Panthers", "cbs": "Columbus Bluejackets", "min": "Minnesota Wild"}


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
                "error.html", e="Jotain mystistä tapahtui..")
        return render_template("index.html", user_data=user_data)
    else:
        return render_template("login.html")


@app.route("/menu")
def menu():
    """
    Main Menu

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
    # TODO tarkista ensin löytyykö annettu id pelaajalistasta!

    # TODO onko tarpeellinen loggaus?
    logging.info("Haetaan pelaajan %s tiedot" % player_id)
    all_seasons = fetch_from_api("/api/json/players/%s" % player_id)
    if not all_seasons:
        # TODO all_seasons voi olla None tai tyhjä tietorakenne;
        # jälkimmäisessä tapauksessa pelaaja ei ole pelannut yhtään ottelua,
        # tulee käsitellä!
        abort(400)
    season_games = fetch_from_api(
        "/api/json/games?pid=%s&year=2012" % player_id)
    latest_game = get_latest_game(season_games)

    name = all_players[str(player_id)]['name']
    position = all_players[str(player_id)]['pos']
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

    # Tarkistetaan onko joukkue seurattavien listalla
    following = False
    if player_id in session['players']:  # TODO testaa toimiiko sessioilla
        following = True

    return render_template(
        "player.html",
        name=name,
        team=team,
        this_season=this_season,
        all_seasons=career_list,
        position=position,
        career=career,
        latest_game=latest_game,
        following=following,
        pid=player_id)


@app.route("/team")
def team_search():
    '''
    Joukkuehaku.

    Kaikki joukkueet listattuna ja suodatettavissa hakuehdolla.
    '''
    return render_template("team_search.html", teams=TEAMS)


@app.route("/team/<team>")
def team(team, year="2012"):
    '''
    Yksittäisen joukkueen tiedot.

    Käyttäjä voi lisätä/poistaa pelaajan seurattavien pelaajien listasta, joka
    on talletettuna sessioon.
    '''
    logging.info("Haetaan joukkueen %s tiedot vuodelta %s" % (team, year))
    stats = fetch_from_api("/api/json/teams?team=%s&year=%s" % (team, year))
    if not stats:
        abort(400)
    season_games = fetch_from_api("/api/json/games?team=%s&year=2012" % (team))
    latest_game = get_latest_game(season_games)

    #Haetaan joukkueen pelaajat ja maalivahdit
    all_players = fetch_from_api(
        "/api/json/top?sort=team&year=2012&goalies=0&limit=1000")
    all_goalies = fetch_from_api(
        "/api/json/top?sort=team&year=2012&goalies=1&limit=1000")
    team_players = []
    for player_dict in all_players:
        if (player_dict['team'] == team):
            team_players.append(player_dict)
    for g in all_goalies:
        if (g['team'] == team):
            team_players.append(player_dict)

    name = TEAMS[team]

    # Tarkistetaan onko joukkue seurattavien listalla
    following = False
    if team in session['teams']:  # TODO testaa toimiiko sessioilla
        following = True

    return render_template(
        "team.html",
        team=team,
        name=name,
        stats=stats,
        year=year,
        latest_game=latest_game,
        players=team_players,
        following=following)


@app.route("/game/<game_id>")
def game(game_id):
    '''
    Yksittäisen ottelun tiedot.
    '''
    logging.info("Haetaan pelin %s tiedot" % game_id)
    game = fetch_from_api("/api/json/games/%s" % game_id)
    if not game:
        abort(400)

    date = game_id
    home_team = game['home_team']
    home_score = game['home_score']
    away_team = game['away_team']
    away_score = game['away_score']

    # Lisätään dictionaryyn eräkohtaisesti listat maaleista, avain = int
    goals_dict = {}
    for v in game['goals']:
        period = v['period']
        if not period in goals_dict:  # Jos ensimmäinen erän maali
            goals_dict[period] = [v]  # tehdään uusi lista
        else:
            goals_dict[period].append(v)  # Loput maalit lisätään listaan

    shootout = []  # Jos pelissä ei tullut shootoutteja, viedään tyhjä lista
    shootout = game['shootout']

    # Poistetaan pelaaja-lista-dictionary -rakenteesta yksi dictionary-taso,
    # jotta Jinja template-engine osaa loopata tietorakenteen läpi ilman
    # ongelmaa.
    skater_list = []
    for k, v in game['skaters'].iteritems():
        new_dict = v
        new_dict['id'] = k
        skater_list.append(new_dict)

    # Järjestetään pelaajalista
    skater_list = sorted(skater_list, key=lambda x: x["pts"], reverse=True)

    return render_template(
        "game.html",
        date=date,
        home_team=home_team,
        home_score=home_score,
        away_team=away_team,
        away_score=away_score,
        goals=goals_dict,
        skaters=skater_list,
        shootout=shootout)


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
# teams-listan joukkuuet lajitellaan teams_dict-dictionaryyn divisioonan mukaan
    for k, v in teams:
        div = v["div"]
        v["team"] = k
        if not div in teams_dict:
            teams_dict[div] = [v]
        else:
            teams_dict[div].append(v)

    return render_template("standings.html", teams=teams_dict, year=year)


@app.route("/top")
def search():
    '''
    TODO: TOP-lista
    '''
    return render_template("top.html")


### Error handlers ###
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', e=e), 404


@app.errorhandler(400)
def bad_request(e):
    return render_template('error.html', e=e), 400
