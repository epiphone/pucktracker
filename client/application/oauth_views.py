# -*-coding:utf-8-*-
"""
URL-reititykset ja sivut OAuthin osalta.

"""

from application import app
from urlparse import parse_qs
from flask import session, redirect, request, url_for
from settings import REQUEST_TOKEN_URL, ACCESS_TOKEN_URL, AUTHORIZE_URL
from settings import CALLBACK_URL, API_URL
from utils import fetch_from_api_signed, get_followed, logged_in, add_followed
from utils import remove_followed
import time


@app.before_request
def before_request():
    """
    Jokaisen HTTP-pyynnön alussa tarkistetaan onko käyttäjä kirjautunut,
    (onko sessiotiedoissa access token ja secret), ja jos ei ole,
    ohjataan kirjautumissivulle.
    """
    if request.endpoint in ["index", "login", "callback"]:
        pass
    elif not logged_in():
        return redirect(url_for("index"))


@app.route("/test_user_remove/<ident>")
def test_user_reset(ident):
    """
    Testifunktio TODO: poista
    """
    param = request.args.get("ids_only", "0")
    ids_only = True if param == "1" else False

    return str(remove_followed(ident, ids_only))


@app.route("/test_user/<ident>")
def test_add_pid(ident):
    """
    Testifunktio TODO: poista
    """
    param = request.args.get("ids_only", "0")
    ids_only = True if param == "1" else False

    return str(add_followed(ident, ids_only))


@app.route("/test_user")
def test_user():
    """
    Testifunktio TODO: poista
    """
    param = request.args.get("ids_only", "0")
    ids_only = True if param == "1" else False

    followed = get_followed(ids_only)
    if not followed:
        # TODO virheidenkäsittely
        pass

    return str(get_followed(ids_only))


@app.route("/login")
def login():
    """
    Haetaan Request Token OAuth-providerilta, ohjataan
    käyttäjä providerin auktorisointisivulle.
    """
    # Haetaan Request Token:
    resp = fetch_from_api_signed(
        base_url=REQUEST_TOKEN_URL,
        callback=CALLBACK_URL)
    if resp.status_code != 200:
        return "Virhe! OAuth Provider ei vastaa"  # TODO

    # Poimitaan vastauksesta Request Token ja Token Secret:
    query_params = parse_qs(resp.content)
    if query_params["oauth_callback_confirmed"][0] != "true":
        return query_params["oauth_callback_confirmed"][0]  # TODO
    oauth_token = query_params["oauth_token"][0]
    oauth_token_secret = query_params["oauth_token_secret"][0]
    assert oauth_token and oauth_token_secret

    # Tallennetaan Request Token Secret sessioon:
    session["req_token_secret"] = oauth_token_secret

    # Ohjataan käyttäjä providerin kirjautumissivulle:
    url = API_URL + AUTHORIZE_URL + "?oauth_token=" + oauth_token
    return redirect(url)


@app.route("/callback")
def callback():
    """
    Haetaan providerilta url-parametrien Request Tokenia vastaava Access Token.

    Tälle sivulle ohjataan, kun sovellukselle on myönnetty
    käyttöoikeudet OAuth-providerin sivuilla.
    """
    oauth_token = request.args.get("oauth_token", "")
    oauth_verifier = request.args.get("oauth_verifier", "")

    for i in range(3):
        if not "req_token_secret" in session:
            time.sleep(1)
        else:
            oauth_token_secret = session["req_token_secret"]
            break
    if not oauth_token_secret:
        return "req_token_secretiä ei löydy", 503

    assert all(x for x in [oauth_token, oauth_verifier,
        oauth_token_secret])  # TODO

    # Haetaan Access Token:
    resp = fetch_from_api_signed(
        base_url=ACCESS_TOKEN_URL,
        token=oauth_token,
        secret=oauth_token_secret,
        verifier=oauth_verifier)
    if resp.status_code != 200:
        return resp.content, resp.status_code

    # Tallennetaan access token & secret sessioon:
    query_params = parse_qs(resp.content)
    session["acc_token"] = query_params["oauth_token"][0]
    session["acc_token_secret"] = query_params["oauth_token_secret"][0]
    return redirect("/")


@app.route("/protected")
def protected():
    """
    Testifunktio - yritetään hakea API:lta OAuthilla suojattua dataa.
    """
    url = API_URL + "/protected"
    token = session["acc_token"]
    token_s = session["acc_token_secret"]
    resp = fetch_from_api_signed(
        base_url=url,
        token=token,
        secret=token_s,
        method="GET")
    return str(resp.status_code) + "<br>" + resp.content


@app.route("/logout")
def logout():
    """
    Kirjaa käyttäjän ulos, uudelleenohjaa kirjautumissivulle.
    """
    session["req_token"] = None
    session["acc_token"] = None
    session["acc_token_secret"] = None
    session["name"] = None
    return redirect(url_for("index"))
