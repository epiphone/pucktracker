# -*-coding:utf-8-*-
"""
A demonstrative OAuth client to use with our provider

This serves as a base, use hmac_client.py, rsa_client.py or
plaintext_client.py depending on which signature type you wish to test.
"""
import requests
#from requests.auth import OAuth1
from requests_oauthlib import OAuth1
from flask import Flask, redirect, request, g, session
from urlparse import parse_qsl, urlparse

app = Flask(__name__)
app.config.update(
    SECRET_KEY="not very secret"
)

PROVIDER_URL = "http://www.pucktracker.appspot.com"
CLIENT_URL = None
if not CLIENT_URL:
    raise Exception("CLIENT_URL muuttuja tulee asettaa.")


ts = None
client = None

@app.route("/start")
def start():
    client = OAuth1(
        app.config["CLIENT_KEY"],
        callback_uri="http://130.234.180.42:5001/callback",
        **app.config["OAUTH_CREDENTIALS"])

    r = requests.post(PROVIDER_URL + "/request_token", auth=client)
    if r.status_code in [400, 401]:
        return "FAIL\n" + r.content
    data = dict(parse_qsl(r.content))
    resource_owner = data.get(u'oauth_token')
    token_secret = data.get('oauth_token_secret').decode(u'utf-8')

    # Token secretiä ei voida tallentaa sessioon tai g-muuttujaan,
    # koska callback-funktion (jossa kys. muuttujaa tarvitaan) kutsutaan
    # Oauth Providerin palvelimelta, jolloin kyseessä on eri sessio.
    # Tilapäisratkaisuna käytetään globaalia muuttujaa.
    global ts
    ts = token_secret
    assert resource_owner is not None and token_secret is not None
    url = PROVIDER_URL + "/authorize?oauth_token=" + resource_owner
    return redirect(url)


@app.route("/callback")
def callback():
    # Extract parameters from callback URL
    data = dict(parse_qsl(urlparse(request.url).query))
    resource_owner = data.get(u'oauth_token').decode(u'utf-8')
    verifier = data.get(u'oauth_verifier').decode(u'utf-8')
    global ts
    token_secret = ts

    # Request the access token
    client = OAuth1(
        app.config["CLIENT_KEY"],
        resource_owner_key=resource_owner,
        resource_owner_secret=token_secret,
        verifier=verifier,
        **app.config["OAUTH_CREDENTIALS"])
    r = requests.post(PROVIDER_URL + "/access_token", auth=client)

    if r.status_code in [400, 401]:
        return "FAIL \n" + r.content
    # Extract the access token from the response
    data = dict(parse_qsl(r.content))
    resource_owner = data.get(u'oauth_token').decode(u'utf-8')
    resource_owner_secret = data.get(u'oauth_token_secret').decode(u'utf-8')
    global client
    client = OAuth1(
        app.config["CLIENT_KEY"],
        resource_owner_key=resource_owner,
        resource_owner_secret=resource_owner_secret,
        **app.config["OAUTH_CREDENTIALS"])
    r = requests.get(PROVIDER_URL + "/protected", auth=client)
    # r = requests.get(PROVIDER_URL + "/protected_realm", auth=client)
    return r.content


@app.route("/test")
def test():
    global client
    if not client:
        return "Clientiä ei ole määritelty - autorisointi on tekemättä"
    r = requests.get(PROVIDER_URL + "/protected", auth=client)
    return r.content
