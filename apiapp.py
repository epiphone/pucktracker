# -*-coding:utf-8-*-
# Sovellus rajapinnan testaamista varten.

import web
import logging
import json
import scrapetest as scraper
from uuid import uuid4
import time
import hmac
import base64
import hashlib
import urllib2
from google.appengine.api import urlfetch
import urlparse
from gaesessions import get_current_session

# Luetaan oAuth-isännän (Twitter) tiedot:
f = open("twitter-tiedot.txt")
CONSUMER_KEY = f.readline().strip().split("=")[-1]
CONSUMER_SECRET = f.readline().strip().split("=")[-1]
REQUEST_TOKEN_URL = f.readline().strip().split("=")[-1]
AUTHORIZE_URL = f.readline().strip().split("=")[-1]
ACCESS_TOKEN_URL = f.readline().strip().split("=")[-1]
f.close()
CALLBACK_URL = "http://130.234.180.42:8080/login"  # Tähän joku fiksumpi tapa.


urls = (
    "/", "Index",
    "/login", "Login",
    "/api/players/(\d+)", "Player",
    "/api/teams/(\w+)",   "Team",
    "/api/games/(\d+)",   "Game"
)

app = web.application(urls, globals())
gae_app = app.gaerun()  # Tämä takaa GAE-yhteensopivuuden.


# TODO yksi funktio allekirjoitetun pyynnön lähettämistä varten

class Login:
    def GET(self):
        """Tälle sivulle ohjataan, kun sovellukselle on myönnetty
        käyttöoikeudet Twitterin sivuilla.
        Haetaan url-parametrien Request Tokenia vastaava Access Token."""
        oauth_token = web.input().oauth_token
        oauth_verifier = web.input().oauth_verifier
        url = ACCESS_TOKEN_URL + "?oauth_verifier=" + oauth_verifier
        params = {
            "oauth_consumer_key": CONSUMER_KEY,
            "oauth_nonce": create_nonce(),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(time.time()).split(".")[0],
            "oauth_token": oauth_token,
            "oauth_version": "1.0"
        }
        # Kääritään parametrit yhteen merkkijonoon:
        params_str = "&".join(["%s=%s" % (key, escape(params[key]))
        for key in sorted(params)])
        base_string = "&".join(["POST", escape(REQUEST_TOKEN_URL),
          escape(params_str)])

        # Luodaan allekirjoitus:
        token_secret = get_current_session()["oauth_token_secret"]
        signing_key = CONSUMER_SECRET + "&" + token_secret
        hashed = hmac.new(signing_key, base_string, hashlib.sha1)
        # Lisätään allekirjoitus Authorization-headerin parametreihin:
        params["oauth_signature"] = base64.b64encode(hashed.digest())

        # Kääritään Authorization-headerin parametrit:
        auth_header = "OAuth " + ", ".join(['%s="%s"' %
            (escape(k), escape(v)) for k, v in params.items()])

        # Lähetetään pyyntö Twitterin oAuth-palvelimelle:
        headers = {"Authorization": auth_header}
        response = urlfetch.fetch(url=url,
                                  method=urlfetch.POST,
                                  headers=headers)
        # Toimitaan vastauksen mukaan:
        if response.status_code != 200:
            return response.content
        query_params = urlparse.parse_qs(response.content)
        name = query_params["screen_name"][0]
        uid = query_params["user_id"][0]
        return "Moro %s, user id %s" % (name, uid)

    def POST(self):
        """Kirjaudutaan Twitterin oAuth-palvelun kautta."""
        twitter_login()


def escape(string):
    """Percent-encodes a given string."""
    return urllib2.quote(string, "")


def twitter_login():
    params = {
        "oauth_callback": CALLBACK_URL,
        "oauth_consumer_key": CONSUMER_KEY,
        "oauth_nonce": create_nonce(),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(time.time()).split(".")[0],
        "oauth_version": "1.0"
    }
    params_str = "&".join(["%s=%s" % (key, escape(params[key]))
        for key in sorted(params)])
    base_string = "&".join(["POST", escape(REQUEST_TOKEN_URL),
        escape(params_str)])

    # Luodaan allekirjoitus:
    signing_key = CONSUMER_SECRET + "&"
    hashed = hmac.new(signing_key, base_string, hashlib.sha1)
    # Lisätään allekirjoitus Authorization-headerin parametreihin:
    params["oauth_signature"] = base64.b64encode(hashed.digest())

    # Kääritään Authorization-headerin parametrit:
    auth_header = "OAuth " + ", ".join(['%s="%s"' %
        (escape(k), escape(v)) for k, v in params.items()])

    # Lähetetään pyyntö Twitterin oAuth-palvelimelle:
    headers = {"Authorization": auth_header}
    response = urlfetch.fetch(url=REQUEST_TOKEN_URL,
                              method=urlfetch.POST,
                              headers=headers)
    if response.status_code != 200:
        return response.content

    # Poimitaan vastauksesta Request Token ja Secret:
    query_params = urlparse.parse_qs(response.content)
    oauth_token = query_params["oauth_token"][0]
    oauth_token_secret = query_params["oauth_token_secret"][0]
    if query_params["oauth_callback_confirmed"][0] != "true":
        return query_params["oauth_callback_confirmed"][0]  # TODO
    # Ohjataan käyttäjä Twitterin kirjautumissivulle
    # (Request Token välitetään url:n mukana):
    url = AUTHORIZE_URL + "?oauth_token=" + oauth_token
    # Tallennetaan Request Token ja Secret session-objektiin:
    session = get_current_session()
    session["oauth_token"] = oauth_token
    session["oauth_token_secret"] = oauth_token_secret  # Huono idea tallentaa sessioon?
    raise web.seeother(url)


def create_nonce():
    """Luo uniikin satunnaisen merkkijonon."""
    return hashlib.md5(str(time.time()) + uuid4().hex).hexdigest()


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
               <form action="/login" method="POST">
                <input type="submit" value="Kirjaudu Twitterillä"/>
               </form>
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
