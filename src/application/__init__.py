from flask import Flask

# Debug stuff
# from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.debug import DebuggedApplication

# Settings
import settings

app = Flask('application')
app.config.from_object('application.settings')

import views


# Werkzeug Debugger (only enabled when DEBUG=True)
if app.debug:
    app = DebuggedApplication(app, evalex=True)


# Flask-DebugToolbar (only enabled when DEBUG=True)
# toolbar = DebugToolbarExtension(app)
