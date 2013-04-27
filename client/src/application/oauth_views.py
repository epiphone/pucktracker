# -*-coding:utf-8-*-
"""
URL-reititykset ja sivut OAuthin osalta.
"""

from application import app
from urlparse import parse_qs
from flask import session, redirect, request, render_template
from settings import REQUEST_TOKEN_URL, ACCESS_TOKEN_URL, AUTHORIZE_URL
from settings import CALLBACK_URL, API_URL
from utils import fetch_from_api_signed


# @app.before_request
# def before_request():
#     """
#     Jokaisen HTTP-pyynnön alussa tarkistetaan onko käyttäjä kirjautunut,
#     ja jos on, haetaan tietokannasta käyttäjän profiili ja liitetään se
#     säiekohtaiseen g-muuttujaan, jonka kautta profiiliin päästään helposti
#     käsiksi.
#     """
#     if request.endpoint in ["login", "callback"]:
#         pass
#     elif not ("oauth_token" in session and "oauth_token_secret" in session):
#         return render_template("login.html")


@app.route("/test_user")
def test_user():
    """
    Testifunktio TODO: poista
    """
    if not "oauth_token" in session:
        return "access token required"

    token = session["oauth_token"]
    token_s = session["oauth_token_secret"]
    resp = fetch_from_api_signed(
        url=API_URL + "/api/user",
        token=token,
        secret=token_s,
        method="GET")
    return str(resp.status_code) + "<br>" + resp.content


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
        # TODO 302 yms?
        return "FAIL! status %d<br>%s" % (resp.status_code, resp.content)

    # Poimitaan vastauksesta Request Token ja Token Secret:
    query_params = parse_qs(resp.content)
    if query_params["oauth_callback_confirmed"][0] != "true":
        return query_params["oauth_callback_confirmed"][0]  # TODO
    oauth_token = query_params["oauth_token"][0]
    oauth_token_secret = query_params["oauth_token_secret"][0]
    assert oauth_token and oauth_token_secret

    # Tallennetaan Request Token ja Secret sessioon:
    session["oauth_token"] = oauth_token
    # TODO: huono idea tallentaa sessioon?
    session["oauth_token_secret"] = oauth_token_secret

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
    try:
        oauth_token_secret = session["oauth_token_secret"]
    except KeyError:
        return "oauth_token_secretiä ei löydetty sessiosta"
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
