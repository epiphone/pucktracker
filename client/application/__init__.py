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

# Templaten syntaksiasetuksia:
app.jinja_env.line_statement_prefix = "$"
# Template-enginen apufunktiot ja vakiot käyttöön:
from views import TEAMS
app.jinja_env.globals.update(jinja_utils=jinja_utils, len=len, TEAMS=TEAMS)
# Template-enginen custom-filterit:
app.jinja_env.filters["shorten_name"] = jinja_utils.shorten_name
app.jinja_env.filters["shorten_game"] = jinja_utils.shorten_game
app.jinja_env.filters["year_to_season"] = jinja_utils.year_to_season


# Käynnistetään debug-moodissa:
if app.debug:
    app = DebuggedApplication(app, evalex=True)
