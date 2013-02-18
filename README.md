# Pucktracker

ITKS545 harjoitustyö
Web-sovellus NHL-tilastojen seuraamista varten.

## API

### Pelaaja

    GET /api/players/12?year=season_2012
- Hakee pelaajan ID=12 kauden 2012-13 koko kauden tilastot.
- year-parametri on joko “season_yyyy” tai “postseason_yyyy”
    - http://sports.yahoo.com/nhl/stats/byposition?pos=C,RW,LW,D
- Jos year-parametria ei määritellä, haetaan koko uran tilastot (career totals)
    - http://sports.yahoo.com/nhl/players/4241/career;_ylt=ArHnXt2clBGdpOHBilYYZfJivLYF

<!-- palauttaa listan kaikista pelaajan kausista 1991-2005 -->

    GET /api/players?query=teemu+selanne

- Palauttaa listan pelaajista joiden nimi vastaa hakuehtoa.
    - http://sports.yahoo.com/nhl/players?query=teemu+selänne&type=lastname&first=1

### Joukkue
    GET /api/teams/ana?year=2012
- Hakee joukkueen ana tilastot kaudelta 2012.
    - http://sports.yahoo.com/nhl/standings?year=season_2012
- Jos joukkuetta ei ole määritelty, haetaan kaikki joukkueet.


### Ottelu

    GET /api/games/2012010395
- Hakee tietyn ottelun tiedot.
- http://sports.yahoo.com/nhl/boxscore?gid=2013021013

    GET /api/games?team=pit&year=2011
- Hakee joukkueen pit kauden 2010-11 pelatut ottelut.
    - http://sports.yahoo.com/nhl/teams/pit/schedule?view=print_list&season=2011
- year-parametri on oletuksena nykyinen kausi.

    GET /api/games?pid=3737

- Hakee pelaajan ID=3737 nykyisen kauden pelatut ottelut.
    - http://sports.yahoo.com/nhl/players/3737/gamelog

### Top-listat

    GET /api/top/players?sort=g&order=asc&year=1994&count=100&pos=LW&team=ana

- Hakee parhaat pelaajat parametrien mukaisesti

    GET /api/top/teams?sort=w&order=asc&year=1994&count=10

- Hakee parhaat joukkueet parametrien mukaisesti

### Käyttäjät
    GET /api/user/95932984(?token=???)

- Palauttaa käyttäjän seuraamat pelaajat ja joukkueet

    POST /api/user/95932984

- Lisää käyttäjälle 95932984 parametreinä määritellyn joukkueen/pelaajan seurattavaksi.
- Parametrina myös mahdollisesti token tunnistautumisen vuoksi

    DELETE /api/user/95932984

- Tuodaan parametreinä joukkueID/pelaajaID joka halutaan poistaa käyttäjän seurannasta.
- Tunnistautumis-token.

## Tietokanta
Palvelimen tietokantaan tallennetaan pelkästään tieto käyttäjistä ja heidän preferensseistään.

    Käyttäjä(OauthID, players[], teams[], lastLogin)

- lastLogin: kertoo milloin käyttäjä käytti sovellusta viimeksi, jotta voidaan hakea häntä kiinnostavat uudet tapahtumat ohjelman käynnistyessä.
- Ehkä tieto kunkin pelaajan/joukkueen uusimmasta nähdystä ottelusta. Toisaalta lastLoginillakin sen voisi selvittää, pitää miettiä vaatii vähemmän datapyyntöjä.

## Välimuisti

- Pelaajien kauden pelatut pelit löytyvät avaimella **[pelaajan id][kausi]** 
    - **5002012** hakee pelaajan *500* kauden 2012-13 pelatut pelit
- Joukkueiden pelatut pelit vastaavasti avaimella **[joukkueen tunnus][kausi]**,
    - **tam2011** hakee joukkueen *tam* pelit kaudelta 2010-2011
- Ottelut löytyvät ottelu-id:n perusteella, joka on muotoa **[vuosi][kuukausi][päivä][satunnainen(?) numeroarvo]**
    - Esim. **201201032**
