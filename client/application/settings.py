"""
settings.py

Configuration for Flask app

Important: Place your keys in the secret_keys.py module,
           which should be kept out of version control.
"""

# from secret_keys import TODO

DEBUG = True
SECRET_KEY = 'dev_key_h8hfne89vm'
# CSRF_ENABLED = True
# CSRF_SESSION_LKEY = 'dev_key_h8asSNJ9s9=+'

# Flask-Cache settings
CACHE_TYPE = 'gaememcached'

# API & OAuth settings
API_URL = "http://www.pucktracker.appspot.com"
REQUEST_TOKEN_URL = "/request_token"
ACCESS_TOKEN_URL = "/access_token"
AUTHORIZE_URL = "/authorize"
CALLBACK_URL = "http://www.alvianpe.appspot.com/callback"
CONSUMER_KEY = "gXHWji6o5Cf41Ws60EN2VxtKPJxOhk"
CONSUMER_SECRET = "D4DDD1JUiJlnxJWVcz3rQXEcytNdl9"
