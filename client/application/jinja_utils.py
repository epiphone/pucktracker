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
    '''
    Palauttaa peli-id:n päivämäärä-arvon suomalaisessa pvm-formaatissa
    '''
    year = s[:4]

    if (s[4:5] == '0'):
        month = s[5:6]
    else:
        month = s[4:6]

    if (s[6:7] == '0'):
        day = s[7:8]
    else:
        day = s[6:8]

    return "%s.%s.%s" % (day,month,year)
