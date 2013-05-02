# -*-coding:utf-8-*-
"""
Alustaa Flask-sovelluksen.

"""

from flask import Flask
from werkzeug.debug import DebuggedApplication

# Asetukset ladataan settings.py-tiedostosta:
app = Flask('application')
app.config.from_object('application.settings')

# Sivut
import oauth_views
import views

# Templaten syntaksiasetuksia:
app.jinja_env.line_statement_prefix = "$"
# Template-enginen apufunktiot ja vakiot käyttöön
import jinja_utils
app.jinja_env.globals.update(jinja_utils=jinja_utils)

# Käynnistetään debug-moodissa:
if app.debug:
    app = DebuggedApplication(app, evalex=True)
