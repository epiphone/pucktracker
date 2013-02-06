# -*-coding:utf-8-*-
# Sovellus rajapinnan testaamista varten.

import web
import json
import scrapetest as scraper


urls = (
    "/", "Index",
    "/api/players/(\d+)", "Player",
    "/api/teams/(\w+)",   "Team",
    "/api/games/(\d+)",   "Game"
)

app = web.application(urls, globals())
app = app.gaerun()  # Tämä takaa GAE-yhteensopivuuden.


class Index:
    def GET(self):
        web.header("Content-type", "text/html")
        return """<html><head><meta charset="UTF-8"></head><body>
               <h3>Kokeile esim.</h3>
               <a href="/api/players/500?year=2011">
                 Teemu Selänteen kauden 2011-2012 pelatut ottelut tilastoineen.
               </a><br>
               <a href="/api/teams/bos">
                 Boston Bruinsin tämän kauden pelatut pelit.
               </a><br>
               <a href="/api/games/2012061108">
                 Kauden 2011-2012 Stanley Cup-finaalin tiedot.
               </a>
               """


### API ###

class Player:
    def GET(self, pid):
        """Palauttaa pelaajan valitun kauden pelatut pelit tilastoineen."""
        year = web.input(year=None).year or "2013"
        data = scraper.scrape_player_games(pid, year)
        web.header("Content-Type", "application/json")
        return json.dumps(data)


class Team:
    def GET(self, team):
        """Palauttaa joukkueen valitun kauden pelatut pelit."""
        year = web.input(year=None).year or "2013"
        data = scraper.scrape_team_games(team, year)
        web.header("Content-Type", "application/json")
        return json.dumps(data)


class Game:
    def GET(self, gid):
        """Palauttaa valitun ottelun tiedot."""
        data = scraper.scrape_game(gid)
        web.header("Content-Type", "application/json")
        return json.dumps(data)
