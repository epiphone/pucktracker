"""
settings.py

Configuration for Flask app

Important: Place your keys in the secret_keys.py module,
           which should be kept out of version control.
"""

# from sercret_keys import TODO

DEBUG = True
SECRET_KEY = 'development_key'
# CSRF_ENABLED = True
# CSRF_SESSION_LKEY = 'dev_key_h8asSNJ9s9=+'

# Flask-Cache settings
CACHE_TYPE = 'gaememcached'
