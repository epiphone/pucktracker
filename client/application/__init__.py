# -*-coding:utf-8-*-
"""
Alustaa Flask-sovelluksen.

"""

from flask import Flask
from werkzeug.debug import DebuggedApplication
import jinja_utils

# Asetukset ladataan settings.py-tiedostosta:
app = Flask('application')
app.config.from_object('application.settings')

# Sivut
import oauth_views
import views
from views import TEAMS

# Templaten syntaksiasetuksia:
app.jinja_env.line_statement_prefix = "$"
# Template-enginen apufunktiot ja vakiot käyttöön:
app.jinja_env.globals.update(jinja_utils=jinja_utils, len=len, TEAMS=TEAMS)
# Template-enginen custom-filterit:
app.jinja_env.filters["shorten_name"] = jinja_utils.shorten_name
app.jinja_env.filters["shorten_game"] = jinja_utils.shorten_game

# Käynnistetään debug-moodissa:
if app.debug:
    app = DebuggedApplication(app, evalex=True)
