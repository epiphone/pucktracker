# coding:utf-8
"""
Apufunktioita ja vakioita template-enginelle.

Importataan __init__.py -tiedostossa ja asetetaan globaaleiksi Jinja2:lle
Käyttö Jinjassa:

    {{ jinja_utils.convert_date(latest_game.date) }}

(latest_game on tuotu parametrina render_templaten yhteydessä)
"""
import urllib


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


def shorten_game(game):
    """
    Palauttaa ottelun nimen lyhennetyssä muodossa.

    >>> shorten_game("Winnipeg Jets vs Winnipeg (23-19-3)")
    'vs Winnipeg (23-19-3)'
    """
    try:
        return game[game.index("vs"):]
    except ValueError:
        return game[game.index("@"):]


def year_to_season(year):
    """
    Palauttaa vuoden kaudeksi muokattuna.

    >>> year_to_season("2008")
    '08-09'
    """
    return year[2:] + "-" + str(int(year) + 1)[2:]


def sort_url(new_sort, old_sort, year, goalies, playoffs, reverse, limit):
    """
    Luo top-urlin annettujen parametrien perusteella.

    >>> sort_url("gs", "a", "2011", "1", "0", "0", "12")
    '/top?sort=a&year=2011&goalies=1&playoffs=0&reverse=1&limit=12'
    >>> sort_url("gs", "gs", "2011", "1", "0", "1", "12")
    '/top?sort=gs&year=2011&goalies=1&playoffs=0&reverse=0&limit=12'
    """
    if new_sort == old_sort:
        reverse = "0" if reverse == "1" else "1"
    else:
        reverse = "1"
    params = dict(
        sort=new_sort,
        year=year,
        goalies=goalies,
        playoffs=playoffs,
        reverse=reverse,
        limit=limit)
    return "href=/top?%s" % urllib.urlencode(params)
