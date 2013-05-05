# coding:utf-8
"""
Apufunktioita ja vakioita template-enginelle.

Importataan __init__.py -tiedostossa ja asetetaan globaaleiksi Jinja2:lle
Käyttö Jinjassa:

    {{ jinja_utils.convert_date(latest_game.date) }}

(latest_game on tuotu parametrina render_templaten yhteydessä)
"""


def convert_date(s):
    '''
    Palauttaa peli-id:n päivämäärä-arvon suomalaisessa pvm-formaatissa.
    Peli-id on muodossa YYYYMMDD + 2 satunnaisnumeroa.

    >>> convert_date("2013050408")
    '4.5.2013'
    >>> convert_date("2013042720")
    '27.4.2013'
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

    return "%s.%s.%s" % (day, month, year)


def shorten_name(name):
    """
    Palauttaa nimen lyhennetyssä muodossa.

    >>> shorten_name("aleksi pekkala")
    'A. Pekkala'
    >>> shorten_name("j.t. miller")
    'J.T. Miller'
    """
    names = name.split()
    first_name = names[0]
    if not "." in first_name:
        names[0] = first_name[0] + "."
    return " ".join([n.title() for n in names])
