# -*-coding:utf-8-*-
# Sovellus rajapinnan testaamista varten.

import web
import json
import scraper
from uuid import uuid4
import time
import hmac
import base64
import hashlib
import urllib2
import urlparse
import os
import logging
from google.appengine.api import urlfetch
from gaesessions import get_current_session

# Luetaan oAuth-isännän (Twitter) tiedot:
f = open("twitter-tiedot.txt")
CONSUMER_KEY = f.readline().strip().split("=")[-1]
CONSUMER_SECRET = f.readline().strip().split("=")[-1]
REQUEST_TOKEN_URL = f.readline().strip().split("=")[-1]
AUTHORIZE_URL = f.readline().strip().split("=")[-1]
ACCESS_TOKEN_URL = f.readline().strip().split("=")[-1]
f.close()
if os.environ.get("SERVER_SOFTWARE", "").startswith("Development"):
    import socket
    # ip = socket.gethostbyname(socket.gethostname())
    ip = "130.234.180.42"
    CALLBACK_URL = "http://" + ip + ":8080/login"
else:
    CALLBACK_URL = "http://pucktracker.appspot.com/login"

urls = (
    "/", "Index",
    "/login", "Login",
    "/api/players/(\d+)", "Player",
    "/api/players",       "SearchPlayers",
    "/api/teams/(\w*)",   "Team",
    "/api/games",         "Games",
    "/api/games/(\d+)",   "Game"
)

web.config.debug = True
app = web.application(urls, globals(), autoreload=False)
gae_app = app.gaerun()  # Tämä takaa GAE-yhteensopivuuden.


### UTILITIES ###


def send_signed_request(url, token=None, callback=None, secret=""):
    """Lähetetään allekirjoitettu pyyntö, palautetaan vastaus."""
    params = {
        "oauth_consumer_key": CONSUMER_KEY,
        "oauth_nonce": hashlib.md5(str(time.time()) + uuid4().hex).hexdigest(),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(time.time()).split(".")[0],
        "oauth_version": "1.0"
    }
    if token:
        params["oauth_token"] = token
    elif callback:
        params["oauth_callback"] = callback

    # Kääritään parametrit yhteen merkkijonoon:
    params_str = "&".join(["%s=%s" % (key, escape(params[key]))
        for key in sorted(params)])
    base_string = "&".join(["POST", escape(url),
      escape(params_str)])

    # Luodaan allekirjoitus:
    signing_key = CONSUMER_SECRET + "&" + secret
    hashed = hmac.new(signing_key, base_string, hashlib.sha1)

    # Lisätään allekirjoitus Authorization-headerin parametreihin:
    params["oauth_signature"] = base64.b64encode(hashed.digest())

    # Kääritään Authorization-headerin parametrit:
    auth_header = "OAuth " + ", ".join(['%s="%s"' %
       (escape(k), escape(v)) for k, v in params.items()])

    # Lähetetään pyyntö Twitterin oAuth-palvelimelle, palautetaan vastaus:
    headers = {"Authorization": auth_header}
    return urlfetch.fetch(url=url,
                          method=urlfetch.POST,
                          headers=headers)


def escape(string):
    """Url-enkoodaa annetun merkkijonon."""
    return urllib2.quote(string, "")


### PAGES ###


class Login:
    def GET(self):
        """Haetaan url-parametrien Request Tokenia vastaava Access Token.
        Tälle sivulle ohjataan, kun sovellukselle on myönnetty
        käyttöoikeudet Twitterin sivuilla."""
        oauth_token = web.input().oauth_token
        oauth_verifier = web.input().oauth_verifier
        oauth_token_secret = get_current_session()["oauth_token_secret"]
        url = ACCESS_TOKEN_URL + "?oauth_verifier=" + oauth_verifier
        response = send_signed_request(url=url, token=oauth_token,
            secret=oauth_token_secret)

        if response.status_code != 200:
            return response.content
        query_params = urlparse.parse_qs(response.content)
        name = query_params["screen_name"][0]
        uid = query_params["user_id"][0]
        return "Moro %s, user id %s" % (name, uid)  # TODO

    def POST(self):
        """Haetaan Request Token Twitterin oAuth-palvelimelta, ohjataan
        käyttäjä Twitterin kirjautumissivulle."""
        response = send_signed_request(url=REQUEST_TOKEN_URL,
            callback=CALLBACK_URL)
        if response.status_code != 200:
            return response.content

        # Poimitaan vastauksesta Request Token ja Token Secret:
        query_params = urlparse.parse_qs(response.content)
        if query_params["oauth_callback_confirmed"][0] != "true":
            return query_params["oauth_callback_confirmed"][0]  # TODO
        oauth_token = query_params["oauth_token"][0]
        oauth_token_secret = query_params["oauth_token_secret"][0]

        # Tallennetaan Request Token ja Secret session-objektiin:
        session = get_current_session()
        session["oauth_token"] = oauth_token
        session["oauth_token_secret"] = oauth_token_secret  # Huono idea tallentaa sessioon?

        # Ohjataan käyttäjä Twitterin kirjautumissivulle:
        url = AUTHORIZE_URL + "?oauth_token=" + oauth_token
        raise web.seeother(url)


class Index:
    def GET(self):
        web.header("Content-type", "text/html")
        return """<html><head><meta charset="UTF-8"></head><body>
               <h3>Kokeile esim.</h3>
               <a href="/api/games?pid=500&year=2011">
                 Teemu Selänteen kauden 2011-2012 pelatut ottelut tilastoineen.
               </a><br>
               <a href="/api/games?team=bos">
                 Boston Bruinsin tämän kauden pelatut pelit.
               </a><br>
               <a href="/api/games/2012061108">
                 Kauden 2011-2012 Stanley Cup-finaalin tiedot.
               </a><br>
               <a href="/api/teams/edm?year=2010">
                 Edmontonin joukkuetilastot kaudelta 2010-11.
               </a><br>
               <a href="/api/players?query=smith">
                 Kaikki pelaajat, joiden nimestä löytyy "smith".
               </a><br>
               <form action="/login" method="POST">
                <input type="submit" value="Kirjaudu Twitterillä"/>
               </form>
               """


### API ###


class Player:
    def GET(self, pid):
        """Palauttaa pelaajan valitun kauden tilastot, tai jos kautta ei ole
        määritelty, koko uran tilastot (sisältää myös yksittäiset kaudet)."""
        year = web.input(year=None).year
        if year:
            # TODO
            pass

        data = scraper.scrape_career(pid)
        web.header("Content-Type", "application/json")
        return json.dumps(data)


class SearchPlayers:
    def GET(self):
        """Palauttaa listan pelaajista, joiden nimi vastaa hakuehtoa.
        Tyhjä hakuehto palauttaa kaikki pelaajat."""
        query = web.input(query="").query
        data = scraper.scrape_players(query)
        web.header("Content-Type", "application/json")
        return json.dumps(data)


class Team:
    def GET(self, team):
        """Palauttaa joukkueen valitun kauden tilastot. Jos joukkuetta ei ole
        määritelty, palautetaan kaikki joukkueet."""
        year = web.input(year="season_2012").year
        if not "season_" in year:
            year = "season_" + year
        data = scraper.scrape_standings(year)
        if team:
            if team not in scraper.TEAMS:
                return "{}"
            data = data[team]
        web.header("Content-Type", "application/json")
        return json.dumps(data)


class Games:
    def GET(self):
        """Palauttaa tietyn joukkueen tai pelaajan tietyllä kaudella pelatut
        ottelut."""
        inp = web.input(team="", pid="", year="2012")
        team, pid, year = inp.team, inp.pid, inp.year
        web.header("Content-Type", "application/json")

        if team:
            data = scraper.scrape_games_by_team(team, year)
            return json.dumps(data)
        elif pid:
            data = scraper.scrape_games_by_player(pid, year)
            return json.dumps(data)
        return "{}"


class Game:
    def GET(self, gid):
        """Palauttaa valitun ottelun tiedot."""
        data = scraper.scrape_game(gid)
        web.header("Content-Type", "application/json")
        return json.dumps(data)
