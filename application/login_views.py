# -*- coding: utf-8 -*-
"""
login_views.py
URL-reititykset ja sivut OAuth providerin osalta.

TODO: siistimistä ja kommentteja
"""

from application import app
from models import ResourceOwner as User
from flask import g, render_template, request, redirect, flash, abort, url_for
from google.appengine.api import users

"""
Url-reititys:

URL                 FUNKTIO           KUVAUS
/                   index             Oletussivu
/login              login             Kirjautuminen Google Accountsin kautta
/after_login        create_or_login   Tarkastetaan onko kyseessä ensimmäinen kirjautuminen
/create_profile     create_profile    Profiilin luonti
/profile            edit_profile      Profiilin muokkaaminen
"""


@app.before_request
def before_request():
    g.user = None
    user = users.get_current_user()
    if user:
        g.user = User.query(User.userid == user.user_id()).get()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    """Kirjautuminen Google Accountsin kautta.

    Käyttäjän tulee olla kirjautunut voidakseen mm. rekisteröidä uusia
    asiakkaita tai suorittaa OAuth-autentikointi.

    TODO: oikea login.html-tiedosto?
    """
    next = request.args.get("next", "/")
    if g.user is not None:
        greeting = ("Welcome, %s! (<a href=\"%s\">sign out</a>)" %
                    (g.user.name, users.create_logout_url("/login")))
    else:
        greeting = ("<a href=\"%s\">Sign in or register</a>." %
                    users.create_login_url("/after_login?next=" + next))
    return "<html><body>%s</body></html>" % greeting


@app.route("/after_login")
def create_or_login():
    """Tätä kutsutaan kirjautumisen jälkeen.

    Jos kyseessä on ensimmäinen kirjautumiskerta, ohjataan käyttäjä
    profiilinluomissivulle, muuten jatketaan.
    """
    user = users.get_current_user()
    user_id = user.user_id()
    stored_user = User.query(User.userid == user_id).get()
    next = request.args.get("next", "/")
    if stored_user is not None:
        # User found, no need to create a new user
        flash(u'Successfully signed in')
        g.user = stored_user
        return redirect(next)
    return redirect(url_for('create_profile', next=next,
                            name=user.nickname(),
                            email=user.email()))


@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    """Sivu profiilin luomista varten."""
    if g.user is not None:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        next = request.form["next"]
        if not name:
            flash(u'Error: you have to provide a name')
        elif '@' not in email:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            new_user = User(
                name=name,
                email=email,
                userid=users.get_current_user().user_id())
            new_user.put()
            return redirect(next)
    next = request.args.get("next", "/")
    return render_template('create_profile.html', next_url=next)


@app.route('/profile', methods=['GET', 'POST'])  # TODO: päivittäminen ei toimi
def edit_profile():
    """Profiilin päivittäminen.

    TODO toteutus
    """
    if g.user is None:
        abort(401)
    form = dict(name=g.user.name, email=g.user.email)
    if request.method == 'POST':
        # if 'delete' in request.form:
        #     db_session.delete(g.user)
        #     db_session.commit()
        #     session['openid'] = None
        #     flash(u'Profile deleted')
        #     return redirect(url_for('index'))
        # form['name'] = request.form['name']
        # form['email'] = request.form['email']
        # if not form['name']:
        #     flash(u'Error: you have to provide a name')
        # elif '@' not in form['email']:
        #     flash(u'Error: you have to enter a valid email address')
        # else:
        #     flash(u'Profile successfully created')
        #     g.user.name = form['name']
        #     g.user.email = form['email']
        #     db_session.commit()
        #     return redirect(url_for('edit_profile'))
        return "TODO päivittäminen ei vielä toimi"
    return render_template('edit_profile.html', form=form)


# TODO Logout
# @app.route('/logout')
# def logout():
#     session.pop('openid', None)
#     flash(u'You have been signed out')
#     return redirect(oid.get_next_url())
