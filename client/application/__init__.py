# -*-coding:utf-8-*-
"""
Alustaa Flask-sovelluksen.
"""

from flask import Flask

# Debug stuff
# from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.debug import DebuggedApplication

# Settings
app = Flask('application')
app.config.from_object('application.settings')

import oauth_views
import views


# Werkzeug Debugger (only enabled when DEBUG=True)
if app.debug:
    app = DebuggedApplication(app, evalex=True)


# Flask-DebugToolbar (only enabled when DEBUG=True)
# toolbar = DebugToolbarExtension(app)
