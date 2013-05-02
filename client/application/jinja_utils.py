# coding:utf-8
"""
Apufunktioita ja vakioita template-enginelle.

Importataan __init__.py -tiedostossa ja asetetaan globaaleiksi Jinja2:lle
Käyttö Jinjassa:

    {{ jinja_utils.convert_date(latest_game.date) }}

(latest_game on tuotu parametrina render_templaten yhteydessä)
"""
from views import TEAMS


def convert_date(s):
    return "TODO:suomalainen päivämäärä (%s)" % s
