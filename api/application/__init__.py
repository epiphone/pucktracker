#-*-coding:utf-8-*-
"""
__init__.py
Alustaa Flask-sovelluksen.

"""

from flask import Flask
from werkzeug.debug import DebuggedApplication

app = Flask("application")
app.config.from_object("application.settings")

# Sivut:
import api_views
import login_views
import cron_views

# Käynnistetään debuggaus-tilassa:
if app.debug:
    app = DebuggedApplication(app, evalex=True)
