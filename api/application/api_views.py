# -*-coding:utf-8-*-
"""
views.py
URL-reititykset ja sivut API:n osalta.

Aleksi Pekkala & Jarkko Saltiola
"""

import scraper
from application import app
from flask import render_template, request, jsonify
from provider import GAEProvider

### Utilities ###

logger = app.logger
oauth_provider = GAEProvider(app)

### Pages ###

"""
Url-reititys:

URL                 FUNKTIO           KUVAUS
/api                api_test          API:n infosivu TODO tänne apin dokumentaatio
/api/players/(\d+)  players           Pelaajan valitun kauden tilastot
/api/players        search_players    Lista pelaajista, joiden nimi vastaa hakuehtoa
/api/teams/(\w*)    team              Joukkueen valitun kauden tilastot
/api/games          games             Joukkueen tai pelaajan valitulla kaudella pelaamat ottelut
/api/games/(\d+)    game              Valitun ottelun tilastot
/api/schedule       schedule          Joukkueen tai pelaajan nykyisen kauden tulevat ottelut
"""


@app.route("/protected")
@oauth_provider.require_oauth()
def protected():
    """Testataan OAuthia."""
    return "Autorisointi onnistui!"


@app.route('/api')
def api_test():
    """Examples for API usage"""
    return render_template("api_test.html")


@app.route('/api/players/<int:player_id>')
def players(player_id):
    """Palauttaa pelaajan valitun kauden tilastot, tai jos kautta ei ole
    määritelty, koko uran tilastot (sisältää myös yksittäiset kaudet)."""
    if player_id:
        year = request.args.get("year", "")
        if year:
            logger.debug("TODO Haetaan pelaajan '%s' kautta '%s'" % (player_id, year))
            data = scraper.scrape_career(player)
        else:
            logger.debug("TODO Haetaan pelaajan '%s' kaikki kaudet" % player_id)
            data = scraper.scrape_career(player_id)
        return jsonify(data)  # jsonify asettaa content-typen automaattisesti


@app.route('/api/players')
def search_players():
    """Palauttaa listan pelaajista, joiden nimi vastaa hakuehtoa.
    Tyhjä hakuehto palauttaa kaikki pelaajat."""
    query = request.args.get('query', '')
    data = scraper.scrape_players(query)
    return jsonify(data)


@app.route('/api/teams/<team_id>')
def team(team_id):
    """Palauttaa joukkueen valitun kauden tilastot. Jos joukkuetta ei ole
        määritelty, palautetaan kaikki joukkueet.
        TODO: Playoffit/Kausipisteet"""

    year = request.args.get('year', 'season_2012')  # Defaults to 'season_2012'

    if not "season_" in year:
            year = "season_" + year

    data = scraper.scrape_standings(year)
    if team_id:
        if team_id not in scraper.TEAMS:
            return "{}"
        data = data[team_id]
    return jsonify(data)


@app.route('/api/games')
def games():
    """Palauttaa tietyn joukkueen tai pelaajan tietyllä kaudella pelatut
    ottelut."""

    team = request.args.get('team', '')
    pid = request.args.get('pid', '')
    year = request.args.get('year', '2012')

    if team:
        data = scraper.scrape_games_by_team(team, year)
        return jsonify(data)
    elif pid:
        data = scraper.scrape_games_by_player(pid, year)
        return jsonify(data)
    return "{}"


@app.route('/api/games/<int:game_id>')
def game(game_id):
    """Palauttaa valitun ottelun tilastot."""
    data = scraper.scrape_game(game_id)
    return jsonify(data)


@app.route('/api/schedule')
def schedule():
    """Palauttaa valitun joukkueen/pelaajan nykyisen kauden
    tulevat ottelut (kotijoukkue, vierasjoukkue, aika)."""
    team = request.args.get('team', '')
    pid = request.args.get('pid', '')

    if pid and not team:
        team = scraper.scrape_players()[pid]["team"]
    if team not in scraper.TEAMS:
        return "{}"  # TODO virheilmoitus?
    data = scraper.scrape_schedule()[team]
    return jsonify(data)
