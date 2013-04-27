# -*-coding:utf-8-*-
"""
Tietokannan alustus.

Käyttää App Enginen NoSQL-tyylistä ndb-tietokantaa.

"""

from google.appengine.ext import ndb


class ResourceOwner(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    userid = ndb.StringProperty()
    teams = ndb.StringProperty(repeated=True)
    players = ndb.StringProperty(repeated=True)


class Callback(ndb.Model):
    callback = ndb.StringProperty()


class Nonce(ndb.Model):
    nonce = ndb.StringProperty()
    timestamp = ndb.StringProperty()

    client = ndb.KeyProperty(kind="Client")

    request_token_id = ndb.IntegerProperty()
    request_token = ndb.KeyProperty(kind="RequestToken")

    access_token = ndb.KeyProperty(kind="AccessToken")


class RequestToken(ndb.Model):
    token = ndb.StringProperty()
    verifier = ndb.StringProperty()
    realm = ndb.StringProperty()
    secret = ndb.StringProperty()
    callback = ndb.StringProperty()

    client = ndb.KeyProperty(kind="Client")

    resource_owner = ndb.KeyProperty(kind=ResourceOwner)


class AccessToken(ndb.Model):
    token = ndb.StringProperty()
    realm = ndb.StringProperty()
    secret = ndb.StringProperty()

    client = ndb.KeyProperty(kind="Client")

    resource_owner = ndb.KeyProperty(kind="ResourceOwner")


class Client(ndb.Model):
    client_key = ndb.StringProperty()
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    secret = ndb.StringProperty()
    pubkey = ndb.StringProperty()

    request_tokens = ndb.KeyProperty(kind=RequestToken, repeated=True)
    access_tokens = ndb.KeyProperty(kind=AccessToken, repeated=True)
    callbacks = ndb.KeyProperty(kind=Callback, repeated=True)

    resource_owner = ndb.KeyProperty(kind=ResourceOwner)
