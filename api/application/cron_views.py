# -*-coding:utf-8-*-
"""
URL-reititykset ja sivut cronjobien, eli skeduloitujen palvelintehtävien
osalta.

Cronjobit on listattu cron.yaml-tiedostoon.
"""

from application import app
from flask import request, abort
from models import RequestToken, AccessToken, Nonce
from google.appengine.ext import ndb


@app.route("/cron/clean")
def clean():
    """
    Poistaa Noncet ja Tokenit tietokannan täyttymisen estämiseksi.

    Skeduloitu tehtävä, jota kutsutaan cron.yaml-tiedoston mukaisesti.
    """
    # Sivun kutsuminen onnistuu vain cron-tehtävien kautta:
    gae_header = request.headers.get("X-Appengine-Cron", None)
    if not gae_header:
        abort(404)

    for cls in [Nonce, AccessToken, RequestToken]:
        keys = cls.query().fetch(1000, keys_only=True)
        ndb.delete_multi(keys)
    return "deleted"
