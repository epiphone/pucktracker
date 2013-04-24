# -*-coding:utf-8-*-
"""
models.py
Tietokannan alustus.
Käyttää App Enginen NoSQL-tyylistä Datastorea.
"""

from google.appengine.ext import ndb


class ResourceOwner(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    userid = ndb.StringProperty()


class Callback(ndb.Model):
    callback = ndb.StringProperty()


class Nonce(ndb.Model):
    nonce = ndb.StringProperty()
    timestamp = ndb.StringProperty()

    # TODO: TTL
    client_id = ndb.IntegerProperty()
    client = ndb.KeyProperty(kind="Client")

    request_token_id = ndb.IntegerProperty()
    request_token = ndb.KeyProperty(kind="RequestToken")

    access_token_id = ndb.IntegerProperty()
    access_token = ndb.KeyProperty(kind="AccessToken")


class RequestToken(ndb.Model):
    token = ndb.StringProperty()
    verifier = ndb.StringProperty()
    realm = ndb.StringProperty()
    secret = ndb.StringProperty()
    callback = ndb.StringProperty()

    # TODO: TTL
    client_id = ndb.StringProperty()
    client = ndb.KeyProperty(kind="Client")

    resource_owner_id = ndb.StringProperty()
    resource_owner = ndb.KeyProperty(kind=ResourceOwner)


class AccessToken(ndb.Model):
    token = ndb.StringProperty()
    realm = ndb.StringProperty()
    secret = ndb.StringProperty()

    # TODO: TTL
    client_id = ndb.StringProperty()
    client = ndb.KeyProperty(kind="Client")

    resource_owner_id = ndb.StringProperty()
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

    resource_owner_id = ndb.StringProperty()
    resource_owner = ndb.KeyProperty(kind=ResourceOwner)
