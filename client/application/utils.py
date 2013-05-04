# -*- coding: utf-8 -*-
"""
Apufunktioita, mm. OAuth Client.

"""

import json
import base64
import hashlib
import hmac
from uuid import uuid4
import time
import urllib
from google.appengine.api import urlfetch
from settings import API_URL, CONSUMER_KEY, CONSUMER_SECRET
import logging
from flask import redirect, url_for, session

METHODS = {
    "GET": urlfetch.GET,
    "POST": urlfetch.POST,
    "DELETE": urlfetch.DELETE,
    "PUT": urlfetch.PUT}


def get_latest_game(game_dict):
    '''
    Hakee dictionaryn uusimman pelin.

    Valitaan arvoltaan suurin avain (lukuna).
    '''
    new_game_date = max(game_dict.keys(), key=int)
    new_game = game_dict[new_game_date]
    new_game['date'] = new_game_date
    return new_game
    # lisää aika sinne ja return
      # TODO: tarkista avaimen muoto


def get_followed(ids_only=False):
    """
    Hakee käyttäjän seuraamat pelaajat ja joukkueet APIlta.

    Vaatii kirjautumisen.

    Args:
        ids_only: jos True, ei haeta seurattujen tilastoja, vaan pelkät id:t
    Returns:
        dictionary, jossa avaimina "players", "teams" ja "name"
    """
    if not logged_in():
        return redirect(url_for("index"))

    ids_only = "1" if ids_only else "0"

    resp = fetch_from_api_signed(
        base_url=API_URL + "/api/json/user",
        url_params=dict(ids_only=ids_only),
        token=session["acc_token"],
        secret=session["acc_token_secret"],
        method="GET")

    if resp.status_code != 200:
        return None

    return json.loads(resp.content)


def add_followed(ident, ids_only=False):
    """
    Lisää pelaajan/joukkueen käyttäjän seurattavaksi.

    Paluuarvo on sama kuin get_followed-funktiossa, nyt päivitettynä.
    """
    if not logged_in():
        return redirect(url_for("index"))

    ids_only = "1" if ids_only else "0"

    data = dict(ids_only=ids_only)
    if ident.isalpha():
        data["team"] = ident
    else:
        data["pid"] = ident

    resp = fetch_from_api_signed(
        base_url=API_URL + "/api/json/user",
        token=session["acc_token"],
        secret=session["acc_token_secret"],
        method="POST",
        data=data)

    if resp.status_code != 200:
        return None

    return json.loads(resp.content)


def remove_followed(ident, ids_only=False):
    """
    Poistaa pelaajan/joukkueen käyttäjän seurannasta.

    Paluuarvo on sama kuin get_followed-funktiossa, nyt päivitettynä.
    """
    if not logged_in():
        return redirect(url_for("index"))

    ids_only = "1" if ids_only else "0"

    data = dict(ids_only=ids_only)
    if ident.isalpha():
        data["team"] = ident
    else:
        data["pid"] = ident

    resp = fetch_from_api_signed(
        base_url=API_URL + "/api/json/user",
        token=session["acc_token"],
        secret=session["acc_token_secret"],
        method="DELETE",
        url_params=data)

    if resp.status_code != 200:
        return None

    return json.loads(resp.content)


def fetch_from_api(url, method="GET"):
    """
    Tekee pyynnön pucktracker-API:lle.

    Palauttaa JSONista muokatun python-olion tai None,
    jos pyyntö epäonnistuu.
    """
    if not url.startswith("http://"):
        url = API_URL + url

    logging.info("API-pyynto: " + url)
    method = METHODS[method]

    resp = urlfetch.fetch(
        url=url,
        method=method,
        deadline=30)

    if resp.status_code != 200:
        logging.info("Pyynto epaonnistui " + resp.content)
        return None  # TODO voiko olla muita onnistuneita statuskoodeja?

    return json.loads(resp.content)


def fetch_from_api_signed(base_url, token=None, callback=None, verifier=None,
                          secret="", method="POST", url_params={}, data={}):
    """
    Lähetetään allekirjoitettu pyyntö, palautetaan vastaus.

    Huom! Url-parametrit tulee määrittää url_params-parametrissa,
    ei base_url-parametrin yhteydessä; esim. "...com/?a=10" ei toimi.

    Args:
        base_url: HTTP-pyynnön kohde ilman url-parametreja.
        token: access tai request token.
        callback: url jota OAuth provider kutsuu jos haetaan request tokenia.
        verifier: varmistus jota tarvitaan access tokenia haettaessa.
        secret: arvo jota käytetään OAuth-allekirjoituksessa.
        method: HTTP-metodi.
        url_params: url-parametrit dictionaryssä.
        data: post-parametrit dictionaryssä.
    Returns:
        OAuth-allekirjoitetun HTTP-pyynnön vastaus, tai None,
        jos pyyntö epäonnistuu.
    """
    assert not "?" in base_url  # TODO debug
    assert isinstance(url_params, dict) and isinstance(data, dict)
    if not base_url.startswith("http://"):
        base_url = API_URL + base_url

    # Kerätään allekirjoituksen parametrit:
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

    # Nämä parametrit eivät tule Authorization-headeriin,
    # niitä käytetään vain allekirjoituksessa:
    signature_params = dict(params.items() + url_params.items() + data.items())

    # Kääritään parametrit yhteen merkkijonoon:
    params_str = "&".join(
                    ["%s=%s" % (escape(key), escape(signature_params[key]))
                    for key in sorted(signature_params)])
    base_string = "&".join([method, escape(base_url),
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
    method = METHODS[method]
    headers = {"Authorization": auth_header}

    if data:
        data = urllib.urlencode(data)
    if url_params:
        base_url += "?" + urllib.urlencode(url_params)

    resp = urlfetch.fetch(
        url=base_url,
        method=method,
        headers=headers,
        payload=data,
        deadline=30)
    logging.info("API-pyynto (suojattu): " + resp.url)
    if resp.status_code == 401:
        # OAuth-auktorisointi epäonnistui (mahd. Access Token on vanhentunut),
        # laitetaan käyttäjä kirjautumaan uudestaan:
        return redirect(url_for("logout"))

    return resp


def escape(text):
    """
    Url-enkoodaa annetun merkkijonon.
    """
    return urllib.quote(text, "")


def logged_in():
    """
    Palauttaa True, jos käyttäjä on kirjautunut sisään.
    """
    return "acc_token" in session and session["acc_token"]
