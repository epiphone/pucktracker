# Pucktracker

ITKS545 harjoitustyö - Aleksi Pekkala & Jarkko Saltiola

Web-sovellus NHL-tilastojen seuraamista varten.
RESTful API + OAuth1.0a provider + Mobile client application

## API

### Pelaajan kausittaiset tilastot

    GET /api/players/500?year=2012

- Hakee [pelaajan ID=500 kauden 2012-13 tilastot]((http://pucktracker.appspot.com/api/players/12?year=2012).
- year-parametri on joko vuosi tai "career" uratilastoja varten.
- Jos year-parametria ei määritellä, haetaan joka vuoden tilastot sekä uratilastot.

### Pelaajien haku nimen perusteella

    GET /api/players?query=teemu+selanne

- Palauttaa [listan pelaajista joiden nimi vastaa hakuehtoa](http://pucktracker.appspot.com/api/players?query=teemu+selanne).
- Tyhjä hakuehto palauttaa kaikki pelaajat

### Joukkueen kausittaiset tilastot

    GET /api/teams/ana?year=2012

- Hakee [joukkueen ana tilastot kaudelta 2012](http://pucktracker.appspot.com/api/teams/ana?year=2012).
- Jos joukkuetta ei ole määritelty, haetaan kaikki joukkueet.
- year-parametri on oletuksena nykyinen kausi

### Sarjataulukko (Joukkueiden top-lista)

### Yksittäisen ottelun tiedot

    GET /api/games/2012010395

- Hakee [ottelun tiedot id:n perusteella](http://pucktracker.appspot.com/api/games/2012010395).

### Joukkueen pelatut ottelut

    GET /api/games?team=pit&year=2011

- Hakee [joukkueen pit kauden 2010-11 pelatut ottelut](http://pucktracker.appspot.com/api/games?team=pit&year=2011).
- year-parametri on oletuksena nykyinen kausi.

### Pelaajan pelatut ottelut

    GET /api/games?pid=1453&year=2009

- Hakee [pelaajan ID=3737 kauden 2009-10 pelatut ottelut](http://pucktracker.appspot.com/api/games?pid=1453&year=2009).
- year-parametri on oletuksena nykyinen kausi.


### Top-listat

    GET /api/top/players?sort=g&year=[post]1994&goalies=false

- Hakee parhaat pelaajat parametrien mukaisesti:
    -  Vuosi ja playoffit/kausi
    -  Järjestäminen tietyn attribuutit mukaan
    -  Joko maalivahdit tai sitten kaikki muut pelaajat


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

### Tietokanta
Palvelimen tietokantaan tallennetaan pelkästään tieto käyttäjistä ja heidän preferensseistään.

    Käyttäjä(OauthID, players[], teams[], lastLogin)

- lastLogin: kertoo milloin käyttäjä käytti sovellusta viimeksi, jotta voidaan hakea häntä kiinnostavat uudet tapahtumat ohjelman käynnistyessä.
- Ehkä tieto kunkin pelaajan/joukkueen uusimmasta nähdystä ottelusta. Toisaalta lastLoginillakin sen voisi selvittää, pitää miettiä vaatii vähemmän datapyyntöjä.

### Välimuisti

- Pelaajien kauden pelatut pelit löytyvät avaimella **[pelaajan id][kausi]**
    - **5002012** hakee pelaajan *500* kauden 2012-13 pelatut pelit
- Joukkueiden pelatut pelit vastaavasti avaimella **[joukkueen tunnus][kausi]**,
    - **tam2011** hakee joukkueen *tam* pelit kaudelta 2010-2011
- Ottelut löytyvät ottelu-id:n perusteella, joka on muotoa **[vuosi][kuukausi][päivä][satunnainen(?) numeroarvo]**
    - Esim. **201201032**
