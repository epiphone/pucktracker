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


@app.route('/api/')
def api_test():
    """TODO tämä palauttamaan APIn dokumentaatio."""
    return render_template("api_test.html")


@app.route("/api/players/<pid>")
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


@app.route("/api/players")
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


@app.route("/api/teams")
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


@app.route("/api/games/<int:gid>")
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


@app.route("/api/games")
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


@app.route("/api/schedule")
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


@app.route("/api/top")
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
