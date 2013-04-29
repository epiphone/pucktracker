# -*- coding: latin-1 -*-
"""
URL-reititykset ja sivut OAuth-toimintoja lukuunottamatta.
"""

import logging
from application import app
from urlparse import parse_qs
from flask import render_template, session, redirect, request
from settings import REQUEST_TOKEN_URL, ACCESS_TOKEN_URL, AUTHORIZE_URL
from settings import CALLBACK_URL, API_URL
from utils import fetch_from_api, fetch_from_api_signed, get_latest_game

### SIVUT ###


@app.route("/")
def index():
    """Käyttäjän seuraamien pelaajien ja joukkueiden uusimmat pelit.
    Kirjautumatonta käyttäjää kehotetaan kirjautumaan sisään.
    """
    if "oauth_token" in session:
        return render_template("start.html",authorized=True)

    else:
        return render_template("start.html",authorized=True)  # TODO false


@app.route("/menu")
def menu():
    """ Navigointilinkit eri sivuille.
    """
    return render_template("menu.html")


# TODO: routtaa hakusivu urliin  /player
@app.route("/player/", defaults={'player_id':0})  # TODO: tee fiksummin
@app.route("/player/<int:player_id>")
def player(player_id):
    all_players = fetch_from_api("/api/json/players")
    if player_id:
        logging.info("Haetaan pelaajan %s tiedot" % player_id)
        all_seasons = fetch_from_api("/api/json/players/%s" % player_id)
        season_games = fetch_from_api("/api/json/games?pid=%s&year=2012" % player_id)
        latest_game = get_latest_game(season_games)

        name = all_players[str(player_id)]['name']
        position = all_players[str(player_id)]['pos']
        team = all_players[str(player_id)]['team']

        this_season = all_seasons['2012']
        career = all_seasons['career']
        del all_seasons['career']

        # Poistetaan pelaaja-lista-dictionary -rakenteesta yksi dictionary-taso, jotta
        # Jinja template-engine osaa loopata tietorakenteen läpi ilman ongelmaa.
        career_list = []
        for k,v in all_seasons.iteritems():
            new_dict = v
            new_dict['year'] = k
            career_list.append(new_dict)

        # Järjestetään pelaajalista
        career_list = sorted(career_list, key=lambda x: x["year"], reverse=True)

        return render_template("player.html", name=name,
            team=team,
            this_season=this_season,
            all_seasons=career_list,
            position=position,
            career=career,
            latest_game=latest_game)
    else:
        player_list = []
        for k,v in all_players.iteritems():
            new_dict = v
            new_dict['id'] = k
            player_list.append(new_dict)

        return render_template("player_search.html", players=player_list)


@app.route("/team/", defaults={"team":""})
@app.route("/team/<team>")
def team(team,year="2012"):
    teams = ['njd', 'nyi', 'nyr', 'phi', 'pit', 'bos', 'buf', 'mon', 'ott',
        'tor', 'car', 'fla', 'tam', 'was', 'wpg', 'chi', 'cob', 'det',
        'nas', 'stl', 'cgy', 'col', 'edm', 'min', 'van', 'ana', 'dal',
        'los', 'pho', 'san']

    names = {"bos": "Boston Bruins", "san": "San Jose Sharks", "nas": "Nashville Predators", "buf": "Buffalo Sabres", "cob": "Columbus Blue Jackets", "wpg": "Winnipeg Jets","cgy": "Calgary Flames", "chi": "Chicago Blackhawks", "det": "Detroit Redwings", "edm": "Edmonton Oilers", "car": "Carolina Hurricanes", "los": "Los Angeles Kings", "mon": "Montreal Canadiens", "dal": "Dallas Stars", "njd": "New Jersey Devils", "nyi": "NY Islanders", "nyr": "NY Rangers", "phi": "Philadelphia Flyers", "pit": "Pittsburgh Penguins", "col": "Colorado Avalanche", "stl": "St. Louis Blues", "tor": "Toronto Maple Leafs", "van": "Vancouver Canucks", "was": "Washington Capitals", "pho": "Phoenix Coyotes", "sjs": "San Jose Sharks", "ott": "Ottawa Senators", "tam": "Tampa Bay Lightning", "ana": "Anaheim Ducks", "fla": "Florida Panthers", "atl": "Atlanta Thrashers", "cbs": "Columbus Bluejackets", "min": "Minnesota Wild", "nsh": "Nashville Predators"}

    if team in teams:
        logging.info("Haetaan joukkueen %s tiedot vuodelta %s" % (team,year))
        stats = fetch_from_api("/api/json/teams?team=%s&year=%s" % (team,year))
        season_games = fetch_from_api("/api/json/games?team=%s&year=2012" % (team))
        latest_game = get_latest_game(season_games)
        logging.info(latest_game)

        name = names[team]
        return render_template("team.html",team=team,
           name=name,
           stats=stats,
           year=year,
           latest_game=latest_game
           )
    else:
        return render_template("team_search.html", teams=teams, names=names)


@app.route("/game/<int:game_id>")
def game(game_id):
    # TODO:Hae pelin tiedot apilta
    # print game
    # Muuta json python-olioksi

    # Build list of goal-objects

    # Build list of players
    # game = {"away_team": "njd", "home_score": "6", "shootout": [], "goals": [{"period": 1, "desc": "Dustin Brown 8 (power play) (Assists: Drew Doughty 11, Mike Richards 10)", "team": "los", "time": "11:03", "score": "0 - 1"}, {"period": 1, "desc": "Jeff Carter 7 (power play) (Assists: Dustin Brown 11, Mike Richards 11)", "team": "los", "time": "12:45", "score": "0 - 2"}, {"period": 1, "desc": "Trevor Lewis 2 (power play) (Assists: Dwight King 2, Drew Doughty 12)", "team": "los", "time": "15:01", "score": "0 - 3"}, {"period": 2, "desc": "Jeff Carter 8 (Assists: Dustin Brown 12, Anze Kopitar 12)", "team": "los", "time": "1:30", "score": "0 - 4"}, {"period": 2, "desc": "Adam Henrique 5 (Assists: Petr Sykora 3, Alexei Ponikarovsky 8)", "team": "njd", "time": "18:45", "score": "1 - 4"}, {"period": 3, "desc": "Trevor Lewis 3 (empty net) (Assists: Dwight King 3, Jarret Stoll 3)", "team": "los", "time": "16:15", "score": "1 - 5"}, {"period": 3, "desc": "Matt Greene 2 (Unassisted)", "team": "los", "time": "16:30", "score": "1 - 6"} ], "home_team": "los", "skaters": {"3990": {"pts": "2", "team": "home", "fo%": "1.000", "fl": "0", "name": "T. Lewis", "fw": "1", "s": "2", "toi": "14:54", "+/-": "+1", "hits": "4", "pim": "0", "g": "2", "bs": "0", "a": "0", "shifts": "25"}, "3972": {"pts": "0", "team": "away", "fo%": ".000", "fl": "2", "name": "R. Carter", "fw": "0", "s": "0", "toi": "08:20", "+/-": "-1", "hits": "0", "pim": "12", "g": "0", "bs": "0", "a": "0", "shifts": "12"}, "1333": {"pts": "1", "team": "away", "fo%": "-", "fl": "0", "name": "P. Sykora", "fw": "0", "s": "1", "toi": "11:53", "+/-": "+1", "hits": "0", "pim": "2", "g": "0", "bs": "0", "a": "1", "shifts": "20"}, "2121": {"pts": "0", "team": "home", "fo%": "-", "fl": "0", "name": "W. Mitchell", "fw": "0", "s": "2", "toi": "24:29", "+/-": "+2", "hits": "0", "pim": "0", "g": "0", "bs": "0", "a": "0", "shifts": "31"}, "3871": {"pts": "0", "team": "away", "fo%": "-", "fl": "0", "name": "A. Greene", "fw": "0", "s": "2", "toi": "19:29", "+/-": "0", "hits": "1", "pim": "0", "g": "0", "bs": "2", "a": "0", "shifts": "29"}, "3657": {"pts": "0", "team": "away", "fo%": ".412", "fl": "10", "name": "T. Zajac", "fw": "7", "s": "1", "toi": "18:47", "+/-": "-2", "hits": "4", "pim": "0", "g": "0", "bs": "0", "a": "0", "shifts": "29"}, "5190": {"pts": "0", "team": "away", "fo%": "-", "fl": "0", "name": "M. Fayne", "fw": "0", "s": "0", "toi": "16:20", "+/-": "+1", "hits": "1", "pim": "0", "g": "0", "bs": "2", "a": "0", "shifts": "26"}, "4424": {"pts": "0", "team": "home", "fo%": "-", "fl": "0", "name": "A. Martinez", "fw": "0", "s": "0", "toi": "15:03", "+/-": "+1", "hits": "3", "pim": "0", "g": "0", "bs": "0", "a": "0", "shifts": "21"}, "4549": {"pts": "0", "team": "home", "fo%": "-", "fl": "0", "name": "S. Voynov", "fw": "0", "s": "2", "toi": "20:00", "+/-": "+2", "hits": "1", "pim": "0", "g": "0", "bs": "2", "a": "0", "shifts": "26"}, "3249": {"pts": "0", "team": "away", "fo%": "-", "fl": "0", "name": "M. Zidlicky", "fw": "0", "s": "2", "toi": "20:20", "+/-": "-1", "hits": "3", "pim": "2", "g": "0", "bs": "2", "a": "0", "shifts": "28"}, "2557": {"pts": "1", "team": "away", "fo%": "-", "fl": "0", "name": "A. Ponikarovsky", "fw": "0", "s": "0", "toi": "15:17", "+/-": "0", "hits": "1", "pim": "0", "g": "0", "bs": "1", "a": "1", "shifts": "19"}, "3565": {"pts": "0", "team": "home", "fo%": "1.000", "fl": "0", "name": "C. Fraser", "fw": "3", "s": "0", "toi": "07:16", "+/-": "0", "hits": "2", "pim": "0", "g": "0", "bs": "0", "a": "0", "shifts": "10"}, "1389": {"pts": "0", "team": "away", "fo%": ".250", "fl": "9", "name": "P. Elias", "fw": "3", "s": "1", "toi": "17:13", "+/-": "0", "hits": "4", "pim": "0", "g": "0", "bs": "1", "a": "0", "shifts": "26"}, "2944": {"pts": "0", "team": "away", "fo%": "-", "fl": "0", "name": "I. Kovalchuk", "fw": "0", "s": "2", "toi": "18:19", "+/-": "-2", "hits": "1", "pim": "0", "g": "0", "bs": "0", "a": "0", "shifts": "24"}, "1920": {"pts": "0", "team": "home", "fo%": "-", "fl": "0", "name": "S. Gagne", "fw": "0", "s": "0", "toi": "08:38", "+/-": "0", "hits": "0", "pim": "0", "g": "0", "bs": "0", "a": "0", "shifts": "11"}, "1753": {"pts": "0", "team": "away", "fo%": "-", "fl": "0", "name": "B. Salvador", "fw": "0", "s": "1", "toi": "20:49", "+/-": "-1", "hits": "3", "pim": "4", "g": "0", "bs": "1", "a": "0", "shifts": "25"}, "5238": {"pts": "1", "team": "away", "fo%": ".500", "fl": "7", "name": "A. Henrique", "fw": "7", "s": "3", "toi": "16:37", "+/-": "+1", "hits": "1", "pim": "0", "g": "1", "bs": "0", "a": "0", "shifts": "25"}, "2528": {"pts": "1", "team": "home", "fo%": ".625", "fl": "6", "name": "J. Stoll", "fw": "10", "s": "3", "toi": "17:43", "+/-": "+1", "hits": "7", "pim": "0", "g": "0", "bs": "1", "a": "1", "shifts": "29"}, "1485": {"pts": "0", "team": "away", "fo%": ".000", "fl": "1", "name": "D. Zubrus", "fw": "0", "s": "1", "toi": "16:41", "+/-": "0", "hits": "6", "pim": "0", "g": "0", "bs": "0", "a": "0", "shifts": "27"}, "3351": {"pts": "3", "team": "home", "fo%": ".000", "fl": "1", "name": "D. Brown", "fw": "0", "s": "2", "toi": "19:23", "+/-": "+1", "hits": "4", "pim": "4", "g": "1", "bs": "1", "a": "2", "shifts": "26"}, "2151": {"pts": "0", "team": "away", "fo%": "-", "fl": "0", "name": "H. Tallinder", "fw": "0", "s": "0", "toi": "18:39", "+/-": "-1", "hits": "2", "pim": "0", "g": "0", "bs": "1", "a": "0", "shifts": "25"}, "3355": {"pts": "0", "team": "away", "fo%": "-", "fl": "0", "name": "Z. Parise", "fw": "0", "s": "1", "toi": "19:12", "+/-": "-2", "hits": "5", "pim": "0", "g": "0", "bs": "1", "a": "0", "shifts": "29"}, "3354": {"pts": "0", "team": "away", "fo%": "-", "fl": "0", "name": "S. Bernier", "fw": "0", "s": "0", "toi": "01:56", "+/-": "0", "hits": "1", "pim": "15", "g": "0", "bs": "0", "a": "0", "shifts": "3"}, "3788": {"pts": "1", "team": "home", "fo%": ".500", "fl": "9", "name": "A. Kopitar", "fw": "9", "s": "2", "toi": "20:15", "+/-": "+1", "hits": "2", "pim": "0", "g": "0", "bs": "2", "a": "1", "shifts": "27"}, "2564": {"pts": "0", "team": "away", "fo%": "-", "fl": "0", "name": "A. Volchenkov", "fw": "0", "s": "0", "toi": "21:28", "+/-": "-2", "hits": "7", "pim": "2", "g": "0", "bs": "4", "a": "0", "shifts": "24"}, "3587": {"pts": "0", "team": "home", "fo%": "-", "fl": "0", "name": "D. Penner", "fw": "0", "s": "2", "toi": "13:36", "+/-": "0", "hits": "2", "pim": "2", "g": "0", "bs": "0", "a": "0", "shifts": "23"}, "4559": {"pts": "2", "team": "home", "fo%": "-", "fl": "0", "name": "D. King", "fw": "0", "s": "2", "toi": "15:36", "+/-": "+1", "hits": "0", "pim": "0", "g": "0", "bs": "0", "a": "2", "shifts": "23"}, "2468": {"pts": "0", "team": "home", "fo%": "-", "fl": "0", "name": "J. Williams", "fw": "0", "s": "2", "toi": "20:24", "+/-": "0", "hits": "2", "pim": "0", "g": "0", "bs": "0", "a": "0", "shifts": "26"}, "3271": {"pts": "1", "team": "home", "fo%": "-", "fl": "0", "name": "M. Greene", "fw": "0", "s": "1", "toi": "14:10", "+/-": "+1", "hits": "2", "pim": "0", "g": "1", "bs": "0", "a": "0", "shifts": "22"}, "4472": {"pts": "2", "team": "home", "fo%": "-", "fl": "0", "name": "D. Doughty", "fw": "0", "s": "1", "toi": "27:31", "+/-": "-1", "hits": "2", "pim": "0", "g": "0", "bs": "1", "a": "2", "shifts": "32"}, "3349": {"pts": "2", "team": "home", "fo%": "1.000", "fl": "0", "name": "J. Carter", "fw": "1", "s": "3", "toi": "16:39", "+/-": "+1", "hits": "0", "pim": "0", "g": "2", "bs": "0", "a": "0", "shifts": "26"}, "3361": {"pts": "2", "team": "home", "fo%": ".769", "fl": "3", "name": "M. Richards", "fw": "10", "s": "1", "toi": "16:55", "+/-": "0", "hits": "0", "pim": "0", "g": "0", "bs": "1", "a": "2", "shifts": "25"}, "4744": {"pts": "0", "team": "away", "fo%": ".333", "fl": "4", "name": "S. Gionta", "fw": "2", "s": "2", "toi": "14:17", "+/-": "-1", "hits": "3", "pim": "0", "g": "0", "bs": "0", "a": "0", "shifts": "20"}, "3741": {"pts": "0", "team": "away", "fo%": ".000", "fl": "1", "name": "D. Clarkson", "fw": "0", "s": "1", "toi": "09:59", "+/-": "-1", "hits": "5", "pim": "10", "g": "0", "bs": "1", "a": "0", "shifts": "14"}, "2837": {"pts": "0", "team": "home", "fo%": "-", "fl": "0", "name": "R. Scuderi", "fw": "0", "s": "0", "toi": "17:01", "+/-": "-1", "hits": "0", "pim": "0", "g": "0", "bs": "1", "a": "0", "shifts": "24"}, "5221": {"pts": "0", "team": "home", "fo%": "-", "fl": "0", "name": "J. Nolan", "fw": "0", "s": "0", "toi": "06:33", "+/-": "0", "hits": "3", "pim": "0", "g": "0", "bs": "0", "a": "0", "shifts": "9"} }, "goalies": {"4147": {"sv%": ".944", "name": "J. Quick", "team": "home", "toi": "59:54", "ga": "1", "sv": "17", "pim": "0", "sa": "18"}, "686": {"sv%": ".792", "name": "M. Brodeur", "team": "away", "toi": "59:24", "ga": "5", "sv": "19", "pim": "0", "sa": "24"} }, "away_score": "1"}
    logging.info("Haetaan pelin %s tiedot" % game_id)
    game = fetch_from_api("/api/json/games/%s" % game_id)
    if game is None:
        return "404, Virheellinen peli"

    home_team = game['home_team']
    home_score = game['home_score']
    away_team = game['away_team']
    away_score = game['away_score']

    goals = game['goals']

    shootout = []  # Jos pelissä ei tullut shootoutteja, viedään tyhjä lista
    shootout = game['shootout']

    # Poistetaan pelaaja-lista-dictionary -rakenteesta yksi dictionary-taso, jotta
    # Jinja template-engine osaa loopata tietorakenteen läpi ilman ongelmaa.
    skater_list = []
    for k,v in game['skaters'].iteritems():
        new_dict = v
        new_dict['id'] = k
        skater_list.append(new_dict)

    # Järjestetään pelaajalista
    skater_list = sorted(skater_list, key=lambda x: x["pts"], reverse=True)

    return render_template("game.html", home_team=home_team,
            home_score=home_score,
            away_team=away_team,
            away_score=away_score,
            goals=goals,
            skaters=skater_list,
            shootout=shootout )


@app.route("/standings/<int:year>")
def standings(year):
    logging.info("Haetaan vuode %s sarjataulukko" % year)
    teams = fetch_from_api("/api/json/teams?&year=%s" % year)

    team_list = []
    for k,v in teams.iteritems():
        new_dict = v
        new_dict['team'] = k
        team_list.append(new_dict)

    team_list = sorted(team_list, key=lambda x: x["pts"], reverse=True)
    return render_template("standings.html",teams=team_list, year=year)


@app.route("/top")
def search():
    return render_template("top.html")
