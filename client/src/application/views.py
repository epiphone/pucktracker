# -*- coding: latin-1 -*-
"""
URL-reititykset ja sivut OAuth-toimintoja lukuunottamatta.
"""

from application import app
from urlparse import parse_qs
from flask import render_template, session, redirect, request
from settings import REQUEST_TOKEN_URL, ACCESS_TOKEN_URL, AUTHORIZE_URL
from settings import CALLBACK_URL, API_URL
from utils import fetch_from_api, fetch_from_api_signed

### SIVUT ###


@app.route("/")
def index():
    """Viimeisimmät ottelutilastot, sarjataulukko ja pelaajien pistekärki.
    käyttäjää kehotetaan kirjautumaan sisään.
    """
    if "oauth_token" in session:
        return render_template("start.html",authorized=True)

    else:
        return render_template("start.html",authorized=True)  # TODO false


@app.route("/player")
def player():
    return render_template("player.html")

@app.route("/game/<int:game_id>")
def game(game_id):
    # TODO:Hae pelin tiedot apilta

    # Muuta json python-olioksi

    # Build list of goal-objects

    # Build list of players

    home_team = "JYP"
    home_score = 99
    away_team = "BOS"
    away_score = 4
    goals = [{"period": 1,
              "desc": "Dustin Brown 8 (power play) (Assists: Drew Doughty 11, Mike Richards 10)",
              "team": "los",
              "time": "11:03",
              "score": "0 - 1"},
             {
               "period": 2,
               "desc": "Adam Henrique 5 (Assists: Petr Sykora 3, Alexei Ponikarovsky 8)",
               "team": "njd",
               "time": "18:45",
               "score": "1 - 4"
             },
             {
               "period": 3,
               "desc": "Trevor Lewis 3 (empty net) (Assists: Dwight King 3, Jarret Stoll 3)",
               "team": "los",
               "time": "16:15",
               "score": "1 - 5"
             }]

    skaters = [{"3990": {"pts": "2", "team": "home", "fo%": "1.000", "fl": "0", "name": "T. Lewis", "fw": "1", "s": "2", "toi": "14:54", "+/-": "+1", "hits": "4", "pim": "0", "g": "2", "bs": "0", "a": "0", "shifts": "25"}, "3972": {"pts": "0", "team": "away", "fo%": ".000", "fl": "2", "name": "R. Carter", "fw": "0", "s": "0", "toi": "08:20", "+/-": "-1", "hits": "0", "pim": "12", "g": "0", "bs": "0", "a": "0", "shifts": "12"}, "1333": {"pts": "1", "team": "away", "fo%": "-", "fl": "0", "name": "P. Sykora", "fw": "0", "s": "1", "toi": "11:53", "+/-": "+1", "hits": "0", "pim": "2", "g": "0", "bs": "0", "a": "1", "shifts": "20"}, "2121": {"pts": "0", "team": "home", "fo%": "-", "fl": "0", "name": "W. Mitchell", "fw": "0", "s": "2", "toi": "24:29", "+/-": "+2", "hits": "0", "pim": "0", "g": "0", "bs": "0", "a": "0", "shifts": "31"}, "3871": {"pts": "0", "team": "away", "fo%": "-", "fl": "0", "name": "A. Greene", "fw": "0", "s": "2", "toi": "19:29", "+/-": "0", "hits": "1", "pim": "0", "g": "0", "bs": "2", "a": "0", "shifts": "29"},"3657": {"pts": "0", "team": "away", "fo%": ".412", "fl": "10", "name": "T. Zajac", "fw": "7", "s": "1", "toi": "18:47", "+/-": "-2", "hits": "4", "pim": "0", "g": "0", "bs": "0", "a": "0", "shifts": "29"}, "5190": {"pts": "0", "team": "away", "fo%": "-", "fl": "0", "name": "M. Fayne", "fw": "0", "s": "0", "toi": "16:20", "+/-": "+1", "hits": "1", "pim": "0", "g": "0", "bs": "2", "a": "0", "shifts": "26"}, "4424": {"pts": "0", "team": "home", "fo%": "-", "fl": "0", "name": "A. Martinez", "fw": "0", "s": "0", "toi": "15:03", "+/-": "+1", "hits": "3", "pim": "0", "g": "0", "bs": "0", "a": "0", "shifts": "21"}}]

    # Poistetaan pelaaja-lista-dictionary -rakenteesta yksi dictionary-taso, jotta
    # Jinja template-engine osaa loopata tietorakenteen läpi ilman ongelmaa.
    skater_list = []
    for d in skaters:
        for d0 in d:
            flatter_dict = dict(id=d0)
            for att in d[d0]:
                flatter_dict[att] = d[d0][att]
            skater_list.append(flatter_dict)
            print "added %s" % d0
        print skater_list

    return render_template("game.html", home_team=home_team ,
                                        home_score=home_score ,
                                        away_team=away_team ,
                                        away_score=away_score,
                                        goals=goals,
                                        skaters=skater_list )


@app.route("/team")
def team():
    return render_template("team.html")

@app.route("/search")
def search():
    return render_template("search.html")
