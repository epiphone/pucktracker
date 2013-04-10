from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.debug import DebuggedApplication

# Debug stuff

app = Flask('application')
app.config.from_object('application.settings')

# Werkzeug Debugger (only enabled when DEBUG=True)
if app.debug:
    app = DebuggedApplication(app, evalex=True)

# Flask-DebugToolbar (only enabled when DEBUG=True)
toolbar = DebugToolbarExtension(app)

### Set up pages ###

import views


## Error handlers
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return "404 - Resource not found", 404


# Handle 500 errors
@app.errorhandler(500)
def server_error(e):
    return "500 - Server error", 500
