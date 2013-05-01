# -*-coding:utf-8-*-
"""
Flask-sovelluksen asetukset.

TODO: avaimet erillisestä moduulista.

"""

DEBUG = True
SECRET_KEY = 'dev_key_h8hfne89vm'
# CSRF_ENABLED = True
# CSRF_SESSION_LKEY = 'dev_key_h8asSNJ9s9=+'

# SERVER_NAME = "alvianpe.appspot.com"  # "www."-alkuinen osoite ei nyt toimi

# API & OAuth asetukset
API_URL = "http://www.pucktracker.appspot.com"
REQUEST_TOKEN_URL = "/request_token"
ACCESS_TOKEN_URL = "/access_token"
AUTHORIZE_URL = "/authorize"
CALLBACK_URL = "http://alvianpe.appspot.com/callback"
CONSUMER_KEY = "yx5S33nebeOELkXSTbEKNZq3G74ihJ"
CONSUMER_SECRET = "6y0dJEKIIPXFdMdHrkIC17RtFyAlaV"
