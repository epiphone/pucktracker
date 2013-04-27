# coding:utf-8
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

METHODS = {
    "GET": urlfetch.GET,
    "POST": urlfetch.POST,
    "DELETE": urlfetch.DELETE,
    "PUT": urlfetch.PUT}


def fetch_from_api(url, method="GET"):
    """Tekee pyynnön pucktracker-API:lle, palauttaa JSONista muokatun
    python-objektin tai None, jos pyyntö epäonnistuu."""
    METHODS[method]
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
    method = METHODS[method]
    headers = {"Authorization": auth_header}
    return urlfetch.fetch(
        url=url,
        method=method,
        headers=headers)


def escape(text):
    """Url-enkoodaa annetun merkkijonon."""
    return urllib.quote(text, "")
