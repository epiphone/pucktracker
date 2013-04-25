# -*- coding: latin-1 -*-
# URL-reititykset ja sivut

import json
import base64
import hashlib
import hmac
from uuid import uuid4
import time
import urllib
from application import app
from urlparse import parse_qs
from flask import render_template, session, redirect, request
from google.appengine.api import urlfetch
from settings import API_URL, CONSUMER_KEY, CONSUMER_SECRET
from settings import REQUEST_TOKEN_URL, ACCESS_TOKEN_URL, AUTHORIZE_URL
from settings import CALLBACK_URL
import logging


### APUFUNKTIOT ###


def fetch_from_api(url, method="GET"):
    """Tekee pyynnön pucktracker-API:lle, palauttaa JSONista muokatun
    python-objektin tai None, jos pyyntö epäonnistuu."""
    method = {"GET": urlfetch.GET, "POST": urlfetch.POST}[method]  # TODO tarvitaanko PUT/HEAD/DELETE?
    response = urlfetch.fetch(API_URL + url, method=method)
    if response.status_code != 200:
        logging.info("Pyyntö epäonnistui " + response.content)  # TODO palautus
        return None  # TODO voiko olla muita onnistuneita statuskoodeja?
    return json.loads(response.content)


def fetch_from_api_signed(url, token=None, callback=None, verifier=None,
    secret="", method="POST"):
    """Lähetetään allekirjoitettu pyyntö, palautetaan vastaus."""
    if not url.startswith("http://"):
        url = API_URL + url
    t = str(time.time()).split(".")[0]
    params = {
        "oauth_consumer_key": CONSUMER_KEY,
        "oauth_nonce": hashlib.md5(t + uuid4().hex).hexdigest(),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": t,
        "oauth_version": "1.0"
    }
    if token:
        params["oauth_token"] = token
    elif callback:
        params["oauth_callback"] = callback
    if verifier:
        params["oauth_verifier"] = verifier
    # Kääritään parametrit yhteen merkkijonoon:
    params_str = "&".join(["%s=%s" % (key, escape(params[key]))
        for key in sorted(params)])
    base_string = "&".join([method, escape(url),
        escape(params_str)])

    # Luodaan allekirjoitus:
    signing_key = CONSUMER_SECRET + "&" + secret
    hashed = hmac.new(signing_key, base_string, hashlib.sha1)

    # Lisätään allekirjoitus Authorization-headerin parametreihin:
    params["oauth_signature"] = base64.b64encode(hashed.digest())

    # Kääritään Authorization-headerin parametrit:
    auth_header = "OAuth " + ", ".join(['%s="%s"' %
       (escape(k), escape(v)) for k, v in params.items()])

    # Lähetetään pyyntö oAuth-providerille, palautetaan vastaus:
    method = {"GET": urlfetch.GET, "POST": urlfetch.POST}[method]  # TODO tarvitaanko PUT/HEAD/DELETE?
    headers = {"Authorization": auth_header}
    return urlfetch.fetch(
        url=url,
        method=method,
        headers=headers)


def escape(text):
    """Url-enkoodaa annetun merkkijonon."""
    return urllib.quote(text, "")

### SIVUT ###


@app.route("/")
def index():
    """Viimeisimmät ottelutilastot, sarjataulukko ja pelaajien pistekärki.
    käyttäjää kehotetaan kirjautumaan sisään.
    """
    if "oauth_token" in session:
        return "Olet autorisoitu."
    else:
        return "Et ole autorisoitu."


@app.route("/login")
def login():
    """Haetaan Request Token OAuth-providerilta, ohjataan
    käyttäjä providerin autorisointisivulle.
    """
    # Haetaan Request Token:
    resp = fetch_from_api_signed(
        url=REQUEST_TOKEN_URL,
        callback=CALLBACK_URL)
    if resp.status_code != 200:
        return "FAIL! status %d<br>%s" % (resp.status_code, resp.content)  # TODO

    # Poimitaan vastauksesta Request Token ja Token Secret:
    query_params = parse_qs(resp.content)
    if query_params["oauth_callback_confirmed"][0] != "true":
        return query_params["oauth_callback_confirmed"][0]  # TODO
    oauth_token = query_params["oauth_token"][0]
    oauth_token_secret = query_params["oauth_token_secret"][0]
    assert oauth_token is not None and oauth_token_secret is not None

    # Tallennetaan Request Token ja Secret sessioon:
    session["oauth_token"] = oauth_token
    session["oauth_token_secret"] = oauth_token_secret  # TODO: huono idea tallentaa sessioon?

    # Ohjataan käyttäjä Twitterin kirjautumissivulle:
    url = API_URL + AUTHORIZE_URL + "?oauth_token=" + oauth_token
    return redirect(url)


@app.route("/callback")
def callback():
    """Haetaan url-parametrien Request Tokenia vastaava Access Token.
    Tälle sivulle ohjataan, kun sovellukselle on myönnetty
    käyttöoikeudet OAuth-providerin sivuilla.
    """
    oauth_token = request.args.get("oauth_token", "")
    oauth_verifier = request.args.get("oauth_verifier", "")
    oauth_token_secret = session["oauth_token_secret"]
    assert not any(x is None or x == "" for x in [oauth_token, oauth_verifier,
        oauth_token_secret])

    url = ACCESS_TOKEN_URL
    resp = fetch_from_api_signed(url=url, token=oauth_token,
        secret=oauth_token_secret, verifier=oauth_verifier)
    if resp.status_code != 200:
        return "FAIL! status %d<br>%s" % (resp.status_code, resp.content)
    query_params = parse_qs(resp.content)
    session["oauth_token"] = query_params["oauth_token"][0]
    session["oauth_token_secret"] = query_params["oauth_token_secret"][0]
    return redirect("/")


@app.route("/protected")
def protected():
    """Testifunktio - yritetään hakea API:lta OAuthilla suojattua dataa."""
    if not "oauth_token" in session:
        return redirect("/")
    url = API_URL + "/protected"
    token = session["oauth_token"]
    token_s = session["oauth_token_secret"]
    resp = fetch_from_api_signed(
        url=url,
        token=token,
        secret=token_s,
        method="GET")
    return str(resp.status_code) + "<br>" + resp.content
