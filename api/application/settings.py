# -*-coding:utf-8-*-
"""
Flask-sovelluksen asetuksia.

"""

DEBUG = True
SECRET_KEY = "development key"  # TODO lue erillisestä moduulista
# CSRF_ENABLED = True
# CSRF_SESSION_LKEY = 'dev_key_h8asSNJ9s9=+'

# Flask-Cache settings
CACHE_TYPE = 'gaememcached'
