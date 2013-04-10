# -*- coding: latin-1 -*-
'''
Author: Jarkko Saltiola
30.3. 2013
'''

'''
views.py
URL route handlers and pages.
'''

from flask import json
# import urlfetch
import scraper
from application import app
from flask import render_template  # Jinja 2
from flask import abort            # Open error site e.g. abort(401)
from flask import request, make_response, flash

### Utilities ###

API = "TODO"
logger = app.logger


@app.after_request
def set_json_header(response):
    '''Set content-type to json for all responses'''
    # Don't touch headers of a html document.
    if (response.data.split('\n',1)[0] != "<!DOCTYPE html>"):  # first line
        response.headers['content-type'] = 'application/json'
        return response
    return response


def debug():
    ''' Open debug view '''
    assert app.debug == False, "Don't panic! You're here by request of debug()"


### Pages ###

@app.route('/')
def index():
    """Examples for API usage"""
    return render_template("api_test.html")


@app.route('/api/players/<int:player_id>')
def players(player_id):
    """Palauttaa pelaajan valitun kauden tilastot, tai jos kautta ei ole
    määritelty, koko uran tilastot (sisältää myös yksittäiset kaudet)."""
    if player_id:
        year = request.args.get('year', '')
        if year:
            logger.debug("TODO Haetaan pelaajan '%s' kautta '%s'" % (player_id,year))
        logger.debug("TODO Haetaan pelaajan '%s' kaikki kaudet" % player_id)
        data = scraper.scrape_career(player_id)
        # response = make_response(json.dumps(data))
        return json.dumps(data)


@app.route('/api/players')
def search_players():
    """Palauttaa listan pelaajista, joiden nimi vastaa hakuehtoa.
    Tyhjä hakuehto palauttaa kaikki pelaajat."""
    query = request.args.get('query', '')
    data = scraper.scrape_players(query)
    # response = make_response(json.dumps(data))
    # response.headers['content-type'] = 'application/json'
    return json.dumps(data)


@app.route('/api/teams/<team_id>')
def team(team_id):
    def add_header(r):
        return r
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
    return json.dumps(data)


@app.route('/api/games')
def games():
    """Palauttaa tietyn joukkueen tai pelaajan tietyllä kaudella pelatut
    ottelut."""

    team = request.args.get('team','')
    pid = request.args.get('pid','')
    year = request.args.get('year','2012')

    if team:
        data = scraper.scrape_games_by_team(team, year)
        return json.dumps(data)
    elif pid:
        data = scraper.scrape_games_by_player(pid, year)
        return json.dumps(data)
    return "{}"


@app.route('/api/games/<int:game_id>')
def game(game_id):
    """Palauttaa valitun ottelun tiedot."""
    data = scraper.scrape_game(game_id)
    return json.dumps(data)


@app.route('/api/schedule')
def schedule():
    """Palauttaa valitun joukkueen/pelaajan nykyisen kauden
    tulevat ottelut (kotijoukkue, vierasjoukkue, aika)."""
    team = request.args.get('team','')
    pid = request.args.get('pid','')

    if pid and not team:
        team = scraper.scrape_players()[pid]["team"]
    if team not in scraper.TEAMS:
        return "{}"  # TODO virheilmoitus?
    data = scraper.scrape_schedule()[team]
    return json.dumps(data)


    # "/api/players/(\d+)", "Player",
    # "/api/players",       "SearchPlayers",
    # "/api/teams/(\w*)",   "Team",
    # "/api/games",         "Games",
    # "/api/games/(\d+)",   "Game",
    # "/api/schedule",      "Schedule"
