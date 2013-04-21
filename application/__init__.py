#-*-coding:utf-8-*-
"""
__init__.py
Alustaa Flask-sovelluksen.
"""

from flask import Flask
from werkzeug.debug import DebuggedApplication

# Debug stuff

app = Flask('application')
app.config.from_object('application.settings')

### Set up pages ###

import api_views
import login_views

## Error handlers  # TODO: Tarviiko nämä määritellä erikseen?
# Handle 404 errors
# @app.errorhandler(404)
# def page_not_found(e):
#     return "404 - Resource not found", 404

# # Handle 500 errors
# @app.errorhandler(500)
# def server_error(e):
#     return "500 - Server error", 500

# Werkzeug Debugger (only enabled when DEBUG=True)
if app.debug:
    app = DebuggedApplication(app, evalex=True)
