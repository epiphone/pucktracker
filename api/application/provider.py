# -*-coding:utf-8-*-
"""
OAuth Providerin implementointi Google App Enginelle.

Perustuu flask-oauthprovider-kirjaston esimerkkiin:
https://github.com/ib-lundgren/flask-oauthprovider

"""


from flask import request, render_template, g, flash, url_for, redirect
from flask.ext.oauthprovider import OAuthProvider
from models import Client, Nonce, Callback
from models import RequestToken, AccessToken
from utils import require_login
from google.appengine.ext import ndb
import time


class GAEProvider(OAuthProvider):

    @property
    def enforce_ssl(self):
        return False

    @property
    def realms(self):
        return []

    @property
    def nonce_length(self):
        return 20, 40

    @require_login
    def authorize(self):
        if request.method == u"POST":
            token = request.form.get("oauth_token")
            return self.authorized(token)
        else:
            token = request.args.get(u"oauth_token", None)
            if token is None:
                return "oauth_token required", 400

            req_token = RequestToken.query(
                RequestToken.token == token).get()
            if req_token is None:
                # Joskus App Enginen datastore ei pysy OAuth-prosessin
                # tahdissa mukana:
                time.sleep(2)
                req_token = RequestToken.query(
                    RequestToken.token == token).get()
                if req_token is None:
                    return "request token not found", 503
            client = req_token.client.get()

            return render_template(
                u"authorize.html",
                token=token,
                req_token=req_token,
                client=client)

    @require_login
    def register(self):
        """Registers a new client (app)."""
        if request.method == u'POST':
            client_key = self.generate_client_key()
            secret = self.generate_client_secret()

            name = request.form.get(u"name")
            description = request.form.get(u"description")
            callback = request.form.get(u"callback")
            pubkey = request.form.get(u"pubkey")

            # Validoitaan syötteet:
            params = [name, description, callback, pubkey]
            if any(not param for param in params):
                flash("Please fill all fields.")
                return redirect(url_for("register"))

            for param in params:
                if len(param) < 5:
                    flash("Input too short: " + param)
                    return redirect(url_for("register"))
                if len(param) > 60:
                    flash("Input too long: ")
                    return redirect(url_for("register"))

            if not callback.startswith("http://"):
                flash("Invalid callback url: " + callback)
                return redirect(url_for("register"))

            info = {
                u"client_key": client_key,
                u"name": name,
                u"description": description,
                u"secret": secret,
                u"pubkey": pubkey
            }
            cb = Callback(callback=callback)
            cb_key = cb.put()
            client = Client(**info)
            client.callbacks.append(cb_key)
            client.resource_owner = g.user.key
            client.put()
            return render_template(u"client.html", **info)
        else:
            clients = Client.query(Client.resource_owner == g.user.key)
            return render_template(u"register.html", clients=clients)

    def validate_timestamp_and_nonce(self, client_key, timestamp, nonce,
            request_token=None, access_token=None):
        token = True
        req_token = True
        client = Client.query(Client.client_key == client_key).get()

        if client:
            nonce = Nonce.query(
                Nonce.nonce == nonce,
                Nonce.timestamp == timestamp,
                Nonce.client == client.key).get()

            if nonce:
                if request_token:
                    req_token = nonce.request_token.get()
                    if req_token and req_token.token == request_token:
                        return False
                if access_token:
                    token = nonce.access_token.get()
                    if token and token.token == access_token:
                        return False
            return True
        else:
            return False

    def validate_redirect_uri(self, client_key, redirect_uri=None):
        try:
            cbs = Client.query(Client.client_key == client_key).get().callbacks
            if redirect_uri in (x.callback for x in ndb.get_multi(cbs)):
                return True

            elif len(cbs) == 1 and redirect_uri is None:
                return True

            else:
                return False

        except AttributeError:  # Clientiä ei löytynyt
            return False

    def validate_client_key(self, client_key):
        return Client.query(Client.client_key == client_key).count() != 0

    def validate_requested_realm(self, client_key, realm):
        return True

    def validate_realm(self, client_key, access_token, uri=None, required_realm=None):
        if not required_realm:
            return True

        client = Client.query(Client.client_key == client_key).get()

        if client:
            token = AccessToken.query(
                AccessToken.token == access_token,
                AccessToken.client == client.key).get()

            if token:
                return token.realm in required_realm

        return False

    @property
    def dummy_client(self):
        """
        Jos OAuth-validointi epäonnistuu, se suoritetaan loppuun dummy-arvoilla
        ajastushyökkäysten estämiseksi.
        """
        return u"dummy_client"

    @property
    def dummy_resource_owner(self):
        return u"dummy_resource_owner"

    def validate_request_token(self, client_key, resource_owner_key):
        token = None
        if client_key:
            client = Client.query(Client.client_key == client_key).get()

            if client:
                token = RequestToken.query(
                    RequestToken.token == resource_owner_key,
                    RequestToken.client == client.key).get()
        else:
            token = RequestToken.query(
                RequestToken.token == resource_owner_key).get()

        return token is not None

    def validate_access_token(self, client_key, resource_owner_key):
        token = None
        client = Client.query(Client.client_key == client_key).get()

        if client:
            token = AccessToken.query(
                AccessToken.client == client.key,
                AccessToken.token == resource_owner_key).get()

        return token is not None

    def validate_verifier(self, client_key, resource_owner_key, verifier):
        token = None
        client = Client.query(Client.client_key == client_key).get()

        if client:
            token = RequestToken.query(
                RequestToken.client == client.key,
                RequestToken.token == resource_owner_key,
                RequestToken.verifier == verifier).get()

        return token is not None

    def get_callback(self, request_token):
        token = RequestToken.query(RequestToken.token == request_token).get()

        if token:
            return token.callback
        else:
            return None

    def get_realm(self, client_key, request_token):
        client = Client.query(Client.client_key == client_key).get()

        if client:
            token = RequestToken.query(
                RequestToken.token == request_token,
                RequestToken.client == client.key).get()

            if token:
                return token.realm

        return None

    def get_client_secret(self, client_key):
        try:
            return Client.query(Client.client_key == client_key).get().secret

        except AttributeError:
            return None

    def get_rsa_key(self, client_key):
        try:
            return Client.query(Client.client_key == client_key).get().pubkey

        except AttributeError:
            return None

    def get_request_token_secret(self, client_key, resource_owner_key):
        client = Client.query(Client.client_key == client_key).get()

        if client:
            token = RequestToken.query(
                RequestToken.client == client.key,
                RequestToken.token == resource_owner_key).get()

            if token:
                return token.secret

        return None

    def get_access_token_secret(self, client_key, resource_owner_key):
        client = Client.query(Client.client_key == client_key).get()

        if client:
            token = AccessToken.query(
                AccessToken.client == client.key,
                AccessToken.token == resource_owner_key).get()

            if token:
                return token.secret

        return None

    def save_request_token(self, client_key, request_token, callback,
            realm=None, secret=None):
        client = Client.query(Client.client_key == client_key).get()

        if client:
            token = RequestToken(
                token=request_token,
                callback=callback,
                secret=secret,
                realm=realm,
                client=client.key)
            token.put()

    def save_access_token(self, client_key, access_token, request_token,
            secret=None):
        client = Client.query(Client.client_key == client_key).get()
        req_token = RequestToken.query(
            RequestToken.token == request_token).get()

        if client and req_token:
            token = AccessToken(
                token=access_token,
                secret=secret,
                client=client.key,
                resource_owner=req_token.resource_owner,
                realm=req_token.realm)
            token.put()

    def save_timestamp_and_nonce(self, client_key, timestamp, nonce,
            request_token=None, access_token=None):
        client = Client.query(Client.client_key == client_key).get()

        if client:
            nonce = Nonce(
                nonce=nonce,
                timestamp=timestamp,
                client=client.key)

            if request_token:
                req_token = RequestToken.query(
                    RequestToken.token == request_token).get()
                nonce.request_token = req_token.key

            if access_token:
                token = AccessToken.query(
                    AccessToken.token == access_token).get()
                nonce.access_token = token.key

            nonce.put()

    def save_verifier(self, request_token, verifier):
        token = RequestToken.query(
            RequestToken.token == request_token).get()
        token.verifier = verifier
        token.resource_owner = g.user.key
        token.put()
