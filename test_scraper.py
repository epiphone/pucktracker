'''
http://css.dzone.com/articles/tdd-python-5-minutes

Tiedoston rakenne:
- Luokka jokaiselle testattavalle funktiolle
    - Funktio jokaiselle testitapaukselle


# This is an empty test-case snippet
class Test(TestCase):
    def test_(self):

        self.assertEqual()

'''

from scraper import *
from unittest import TestCase
import time


class Test_scrape_players(TestCase):
    def test_empty_query(self):
        # should return all players in a dictionary
        print "test_empty_query"
        self.assertNotEqual({}, scrape_players(""))

    def test_unknown_player(self):
        print "test_unknown_player"
        self.assertEqual({}, scrape_players("roope ankka"))

    def test_all_players_are_correct(self):
        all_players = scrape_players("")
        for player in all_players:
            # Check player ID
            self.assertNotEqual(None, re.match(
                    "^\d{2,4}$",
                    player))
            # Check name
            self.assertNotEqual(None, re.match(
                    "[A-Z][A-Za-z.-]+\s[a-z]{0,3}\s?[a-z]{0,3}\s?[A-Z][A-Za-z']+",
                    all_players[player]['name']))
            # Check position
            self.assertNotEqual(None, re.match(
                    "RW|LW|D|C|G",
                    all_players[player]['pos']))
            # Check team name
            self.assertEqual(True, (all_players[player]['team'] in TEAMS))

    def test_cache_is_same(self):
        print "test_cache_is_same"
        noncached = scrape_players("teemu+selanne")
        # sleeptime = 2

        # print "sleeping for %s sec" % sleeptime
        # time.sleep(sleeptime)
        cached = scrape_players("teemu+selanne")
        self.assertEqual(noncached, cached)


    # def test_cache_is_faster(self):
    #     print "test_cache_is_faster"

    #     noncached = scrape_players("teemu+selanne")

    #     cached = scrape_players("teemu+selanne")

    #     self.assertEqual(true, t_cache_hit < t_scrape_site)


'''

class Test_scrape_players_and_stats(TestCase):
    def test_(self):
        self.assertEqual()



class Test_scrape_career(TestCase):
    def test_(self):
        self.assertEqual()


class Test_scrape_games_by_player(TestCase):
    def test_(self):
        self.assertEqual()


class Test_scrape_games_by_team(TestCase):
    def test_(self):
        self.assertEqual()


class Test_scrape_game(TestCase):
    def test_(self):
        self.assertEqual()


class Test_scrape_schedule(TestCase):
    def test_(self):
        self.assertEqual()


class Test_scrape_standings(TestCase):
    def test_(self):
        self.assertEqual()


class Test_get_next_game(TestCase):
    def test_(self):
        self.assertEqual()


class Test_get_latest_game(TestCase):
    def test_(self):
        self.assertEqual()


class Test_add_cache(TestCase):
    def test_(self):
        self.assertEqual()


class Test_toi_to_sec(TestCase):
    def test_(self):
        self.assertEqual()


class Test_sec_to_toi(TestCase):
    def test_(self):
        self.assertEqual()


class Test_str_to_date(TestCase):
    def test_(self):
        self.assertEqual()


class Test_isostr_to_date(TestCase):
    def test_(self):
        self.assertEqual()
'''


# class Memcache():
#     '''For emulating gae's memcache'''

#     def __init__(self):
#         self.store = {}

#     def get(self, key):
#         '''Returns requested key'''
#         if key in self.store:
#             return self.store[key]["value"]
#         else:
#             return None

#     def set(self, key, value, expires=None):
#         '''Set value to memcache'''
#         self.store[key] = {"value": value, "expires": expires}

#     def get_expires(key):
#         if key in self.store:
#             return self.store[key]["expires"]
#         else:
#             print "Kaaos dummy memcachessa"
