# -*-coding:utf-8-*-
"""
Apufunktioita yms.

"""

from functools import wraps
from flask import g, request, redirect
from google.appengine.api import users


def require_login(f):
    """
    Dekoraattori, joka blokkaa kirjautumattomat käyttäjät ja ohjaa
    kirjautumissivulle.

    Perustuu flask-oauthprovider-kirjaston esimerkkiin.
    """
    @wraps(f)
    def decorator(*args, **kwargs):
        if g.user is None:
            next = request.url
            login_url = users.create_login_url("/after_login?next=" + next)
            return redirect(login_url)
        else:
            return f(*args, **kwargs)
    return decorator
