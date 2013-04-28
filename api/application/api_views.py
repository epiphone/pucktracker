# -*-coding:utf-8-*-
"""
URL-reititykset ja sivut API:n osalta.

Aleksi Pekkala & Jarkko Saltiola
"""

import scraper
from application import app
from flask import render_template, request, jsonify, abort, Response
from provider import GAEProvider
import logging
import json
from models import AccessToken


### GLOBAALIT ###

oauth_provider = GAEProvider(app)

### SIVUT ###

"""
Url-reititys:

URL                 FUNKTIO           KUVAUS
/api                api_test          API:n infosivu TODO tänne apin dokumentaatio
/api/players/(\d+)  players           Pelaajan valitun kauden tilastot
/api/players        search_players    Lista pelaajista, joiden nimi vastaa hakuehtoa
/api/teams/(\w+)    team              Joukkueen valitun kauden tilastot
/api/games          games             Joukkueen tai pelaajan valitulla kaudella pelaamat ottelut
/api/games/(\d+)    game              Valitun ottelun tilastot
/api/schedule       schedule          Joukkueen tai pelaajan nykyisen kauden tulevat ottelut
"""


@app.route("/protected")
@oauth_provider.require_oauth()
def protected():
    """Testataan OAuthia."""
    return "Autorisointi onnistui!"


@app.route("/api/")
def api_test():
    """
    API:n "juuri". Palauttaa API:n dokumentaation.
    """
    return render_template("api_documentation.html")


@app.route("/api/json/players/<pid>")
def players(pid):
    """
    Palauttaa pelaajan valitun kauden tilastot, tai jos kautta ei ole
    määritelty, koko uran tilastot (sisältää myös yksittäiset kaudet).
    """
    try:
        data = scraper.scrape_career(pid)
    except Exception as e:
        logging.error(e)
        abort(404)

    if data is None:
        abort(404)

    year = request.args.get("year", None)
    if year:
        if year in data:
            data = data[year]
        else:
            abort(404)

    return jsonify(data)  # jsonify asettaa content-typen automaattisesti


@app.route("/api/json/players")
def search_players():
    """
    Palauttaa listan pelaajista, joiden nimi vastaa hakuehtoa.

    Tyhjä hakuehto palauttaa kaikki pelaajat.
    """
    query = request.args.get('query', '')
    # TODO queryn validointi? Onko tarpeen?
    try:
        data = scraper.scrape_players(query)
    except Exception as e:
        logging.error(e)
        abort(404)

    return jsonify(data)


@app.route("/api/json/teams")
def team():
    """
    Palauttaa joukkueen valitun kauden tilastot.

    Jos joukkuetta ei ole määritelty, palautetaan kaikki joukkueet.
    """
    year = request.args.get("year", scraper.SEASON)
    team = request.args.get("team", None)

    try:
        data = scraper.scrape_standings(year)
    except Exception as e:
        logging.error(e)
        abort(404)
    if data is None:
        abort(404)

    if team:
        if not team in data:
            abort(404)
        data = data[team]

    return jsonify(data)


@app.route("/api/json/games/<gid>")
def game(gid):
    """
    Palauttaa yksittäisen ottelun tiedot.
    """
    try:
        data = scraper.scrape_game(gid)
    except Exception as e:
        logging.error(e)
        abort(404)
    if data is None:
        abort(404)

    return jsonify(data)


@app.route("/api/json/games")
def games():
    """
    Palauttaa valitun joukkueen tai pelaajan valitulla kaudella pelatut
    ottelut.
    """
    team = request.args.get("team", None)
    pid = request.args.get("pid", None)
    year = request.args.get("year", scraper.SEASON)

    if pid:
        func = scraper.scrape_games_by_player
        arg = pid
    elif team:
        if not team in scraper.TEAMS:
            abort(404)
        func = scraper.scrape_games_by_team
        arg = team
    else:
        abort(404)  # Joko team tai pid tulee määrittää

    try:
        data = func(arg, year)
        if data is None:
            abort(404)
    except Exception as e:
        logging.error(e)
        abort(404)

    return jsonify(data)


@app.route("/api/json/schedule")
def schedule():
    """
    Palauttaa valitun joukkueen/pelaajan nykyisen kauden
    tulevat ottelut (kotijoukkue, vierasjoukkue, aika).

    Jos kumpaakaan parametriä ei määritellä, palautetaan kaikki
    tulevat ottelut.
    """
    team = request.args.get("team", None)
    pid = request.args.get("pid", None)

    if pid or team:
        kwargs = {"pid": pid, "team": team}
        try:
            data = scraper.get_next_games(**kwargs)
            if data is None:
                abort(404)
        except Exception as e:
            logging.error(e)
            abort(404)
    else:
        try:
            data = scraper.scrape_schedule()
            if data is None:
                abort(404)
        except Exception as e:
            logging.error(e)
            abort(404)

    return jsonify(data)


@app.route("/api/json/top")
def top():
    """
    Hakee parametrien mukaan määritellyt pelaajat tilastoineen.

    Esim. 30 eniten maaleja tehnyttä kenttäpelaajaa, 15 maalivahtia
    torjuntaprosentin mukaan, jne.
    """
    sort = request.args.get("sort", None)
    year = request.args.get("year", scraper.SEASON)
    try:
        goalies = bool(int(request.args.get("goalies", "0")))
        reverse = bool(int(request.args.get("reverse", "1")))
        playoffs = bool(int(request.args.get("playoffs", "0")))
        limit = int(request.args.get("limit", "30"))
    except ValueError:
        abort(400)  # Bad Request

    allowed_sorts = scraper.GOALIE_STATS if goalies else scraper.PLAYER_STATS
    if sort and sort not in allowed_sorts:
        abort(400)  # TODO pitäisikö palauttaa virheilmoitus?

    try:
        data = scraper.scrape_player_stats(year=year, playoffs=playoffs,
            goalies=goalies, reverse=reverse, order=sort)
        if data is None:
            return "none"
            abort(404)
    except Exception as e:
        logging.error(e)
        abort(404)

    if limit:
        data = data[:limit]

    # Jsonify ei salli listan palauttamista JSON-muodossa, käytetään
    # pythonin omaa JSON-moduulia:
    data = json.dumps(data)
    return Response(data, mimetype="application/json")


@app.route("/api/json/user", methods=["GET", "POST", "DELETE"])
@oauth_provider.require_oauth()
def user():
    """
    Hakee, lisää ja poistaa käyttäjän seuraamia pelaajia/joukkueita.

    Vaatii OAuth-allekirjoitetun pyynnön.
    TODO välimuisti
    """
    # Poimitaan oauth token HTTP-pyynnön Authorization-headerista:
    auth_header = request.headers.get("Authorization", None)
    if not auth_header:
        abort(500)

    for param in auth_header.split():
        if param.startswith("oauth_token"):
            token = param.split("=")[-1][1:-2]
            break

    if not token:
        abort(500)

    # Haetaan tokenia vastaava käyttäjä:
    try:
        acc_token = AccessToken.query(AccessToken.token == token).get()
        user = acc_token.resource_owner.get()
        players, teams = user.players, user.teams
    except KeyError:  # access tokenia tai käyttäjää ei löydy
        abort(500)

    # Poimitaan ids_only-parametri joko urlista tai post-parametreista:
    if "ids_only" in request.form:
        ids_only = request.form["ids_only"]
    else:
        ids_only = request.args.get("ids_only", "0")
    try:
        ids_only = int(ids_only)
    except ValueError:
        abort(400)

    if request.method == "GET":
        # Palautetaan käyttäjän seuraamat pelaajat ja joukkueet:
        if ids_only:
            # Palautetaan vain id:t:
            return jsonify(dict(player=players, teams=teams))

        # Palautetaan id:t sekä tilastot:
        ret = get_players_and_teams(players, teams)
        return jsonify(ret)

    if request.method == "POST":
        # Lisätään seurattava pelaaja tai joukkue:
        if "pid" in request.form:
            pid = request.form["pid"]

            # Validoitaan pelaajan id:
            if pid in players:
                abort(400)  # Pelaaja on jo seurattavien listassa

            all_players = scraper.scrape_players()
            if not pid in all_players:
                abort(400)  # pid:tä vastaavaa pelaajaa ei löydy

            # Lisätään pid käyttäjän seurattavien pelaajien listalle:
            players.append(pid)
            user.players = players
            user.put()

            # Palautetaan päivittynyt seurantalista, kuten GET-pyynnössä:
            if ids_only:
                ret = dict(players=players, teams=teams)
            else:
                ret = get_players_and_teams(players, teams)
            return jsonify(ret)

        if "team" in request.form:
            team = request.form["team"].lower()
            # Validoitaan joukkueen tunnus
            if team in teams:
                abort(400)  # Joukkue on jo seurattavien listassa
            if not team in scraper.TEAMS:
                abort(400)  # Epäkelpo joukkueen tunnus

            # Lisätään joukkue käyttäjän seurattavien joukkueiden listalle:
            teams.append(team)
            user.teams = teams
            user.put()

            # Palautetaan päivittynyt seurantalista, kuten GET-pyynnössä:
            if ids_only:
                ret = dict(players=players, teams=teams)
            else:
                ret = get_players_and_teams(players, teams)
            return jsonify(ret)

        else:
            abort(400)  # Lisättävä pelaaja tai joukkue tulee määrittää

    if request.method == "DELETE":
        # Poistetaan seurattava pelaaja tai joukkue:
        pid = request.args.get("pid", None)
        team = request.args.get("team", None)
        if pid:
            if not pid in players:
                abort(400)  # pelaajaa ei löydy seurattavien listasta
            players.remove(pid)
            user.players = players

        elif team:
            if not team in teams:
                abort(400)  # joukkuetta ei löydy seurattavien listasta
            teams.remove(team)
            user.teams = teams

        else:
            abort(400)  # joko poistettava pelaaja tai joukkue tulee määrittää

        user.put()
        if ids_only:
            ret = dict(players=players, teams=teams)
        else:
            ret = get_players_and_teams(players, teams)
        return jsonify(ret)


def get_players_and_teams(players=None, teams=None):
    """
    Hakee valittujen pelaajien ja joukkueiden kauden tilastot sekä viimeisimmän
    ottelut tiedot.

    Jos pelaaja ei ole pelannut tällä kaudella yhtään ottelua, pelaajan osalta
    palautetaan vain tyhjiöarvo.
    """
    ret = {}
    if teams:
        standings = scraper.scrape_standings()
        if not standings:
            abort(503)  # Service unavailable
        if not all(team in standings for team in teams):
            abort(400)  # Bad request - virheellinen joukkueen tunnus
        for team in teams:
            stats = standings[team]
            gid = scraper.get_latest_game(team=team)
            if not stats or not gid:
                ret[team] = dict(stats=None, latest_game=None)
            else:
                latest_game = scraper.scrape_game(gid) if gid else None
                ret[team] = dict(stats=stats, latest_game=latest_game)

    if players:
        player_stats = scraper.scrape_player_stats()

        for pid in players:
            for pstat in player_stats:
                if pid == pstat["pid"]:
                    gid = scraper.get_latest_game(pid=pid)
                    if not gid:
                        stats, latest_game = None, None
                    else:
                        latest_game = scraper.scrape_game(gid)
                        stats = pstat
                    ret[pid] = dict(stats=stats, latest_game=latest_game)
                    break

        # Seurattavaa pelaajaa ei löytynyt kenttäpelaajista,
        # etsitään maalivahdeista:
        goalie_stats = scraper.scrape_player_stats(goalies=True)

        for pid in players:
            if pid in ret:
                continue  # Pelaaja löytyi kenttäpelaajista
            for pstat in goalie_stats:
                if pid == pstat["pid"]:
                    gid = scraper.get_latest_game(pid=pid)
                    if not gid:
                        stats, latest_game = None, None
                    else:
                        latest_game = scraper.scrape_game(gid)
                        stats = pstat
                    ret[pid] = dict(stats=stats, latest_game=latest_game)
                    break

        # Jos pelaajaa ei löytynyt kenttäpelaajista eikä maalivahdeista,
        # ei pelaaja ole pelannut yhdessäkään ottelussa nykyisellä kaudella
        for pid in players:
            if not pid in ret:
                ret[pid] = dict(stats=None, latest_game=None)

    return ret
