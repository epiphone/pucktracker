# Pucktracker

ITKS545 harjoitustyö - Aleksi Pekkala & Jarkko Saltiola

Web-sovellus NHL-tilastojen seuraamista varten.
RESTful API + OAuth1.0a provider + Mobile client application

## API

### Pelaajan kausittaiset tilastot

    GET /api/players/500?year=2012

- Hakee [pelaajan ID=500 kauden 2012-13 tilastot](http://pucktracker.appspot.com/api/players/12?year=2012).
- year-parametri on joko vuosi tai "career" uratilastoja varten.
- Jos year-parametria ei määritellä, haetaan joka vuoden tilastot sekä uratilastot.

### Pelaajien haku nimen perusteella

    GET /api/players?query=teemu+selanne

- Palauttaa [pelaajat joiden nimi vastaa hakuehtoa](http://pucktracker.appspot.com/api/players?query=teemu+selanne).
- Tyhjä hakuehto palauttaa kaikki pelaajat.

### Joukkueiden kausittaiset tilastot

    GET /api/teams?team=ana&year=2012

- Hakee [joukkueen ana tilastot kaudelta 2012](http://pucktracker.appspot.com/api/teams?team=ana&year=2012).
- Jos joukkuetta ei ole määritelty, haetaan kaikki joukkueet (eli sarjataulukko).
- year-parametri on oletuksena nykyinen kausi.
- team-parametri on jokin seuraavista: njd, nyi, nyr, phi, pit, bos, buf, mon, ott, tor, car, fla, tam, was, wpg, chi, cob, det, nas, stl, cgy, col, edm, min, van, ana, dal, los, pho, san.
- Huom! Sarjataulukkoa haettaessa joukkueet eivät ole missään erityisessä järjestyksessä; järjestäminen jää asiakkaan vastuulle.

### Yksittäisen ottelun tiedot

    GET /api/games/2012010395

- Hakee [ottelun tiedot id:n perusteella](http://pucktracker.appspot.com/api/games/2012010395).

### Joukkueen pelatut ottelut

    GET /api/games?team=pit&year=2011

- Hakee [joukkueen pit kauden 2010-11 pelatut ottelut](http://pucktracker.appspot.com/api/games?team=pit&year=2011).
- year-parametri on oletuksena nykyinen kausi.
- team-parametri on jokin seuraavista: njd, nyi, nyr, phi, pit, bos, buf, mon, ott, tor, car, fla, tam, was, wpg, chi, cob, det, nas, stl, cgy, col, edm, min, van, ana, dal, los, pho, san.


### Pelaajan pelatut ottelut

    GET /api/games?pid=1453&year=2009

- Hakee [pelaajan ID=3737 kauden 2009-10 pelatut ottelut](http://pucktracker.appspot.com/api/games?pid=1453&year=2009).
- year-parametri on oletuksena nykyinen kausi.
- Huom! Jos api/games-urlissa on parametreina sekä "team" että "pid", käytetään "pid":tä.

### Joukkueen tulevat ottelut

    GET /api/schedule?team=bos

- Hakee joukkueen bos tämän kauden **tulevat** ottelut.

### Pelaajan tulevat ottelut

    GET /api/schedule?pid=500

- Hakee joukkueen pelaajan ID=500 tämän kauden **tulevat** ottelut.
- Huom! Jos api/games-urlissa on parametreina sekä "team" että "pid", käytetään "pid":tä.

### Otteluohjelma

    GET /api/schedule

- Jos kumpaakaan (**pid** tai **team**) parametria ei ole määritelty, haetaan kaikki tulevat ottelut.

### Top-pelaajat

    GET /api/top?sort=ga&reverse=1&year=2008&goalies=1&playoffs=1&limit=10

- Hakee [parhaat pelaajat parametrien mukaisesti](http://pucktracker.appspot.com/api/top?sort=g&reverse=1&year=2008&goalies=1&playoffs=1&limit=10):
    -  year määrittää kauden, oletuksena nykyinen kausi.
    -  sort määrittää järjestyksen, vaihtoehdot ovat
        - pelaajilla  name, team, gp, g, a, pts, +/-, pim, hits, bks, fw, fl, fo%, ppg, ppa, shg, sha, gw, sog, pct
            - oletuksena **pts**.
        - maalivahdeilla name, team, gp, gs, min, w, l, otl, ega, ga, gaa, sa, sv, sv%, so
           - oletuksena **w**.
    -  goalies (arvo 0 tai 1) määrittää haetaanko maalivahteja; oletuksena ei haeta.
    - playoffs (0 tai 1) määrittää haetaanko valitun kauden playoffien top-listoja; oletuksena ei.
    - reverse (0 tai 1) määrittää järjestyksen suunnan, oletuksena reverse=1, eli suurin arvo ensin.
    - limit määrittää tulosten maksimimäärän, oletuksena 30.
- Huom! Paluuarvo on poikkeuksellisesti lista (TODO: turvallisuussyy?).


### Käyttäjän seuraamat pelaajat/joukkueet

    GET /api/user?pids_only=1

- Palauttaa käyttäjän seuraamat pelaajat ja joukkueet.
- Oletuksena palautetaan seurattavien pelaajien sekä joukkueiden nykyisen kauden tilastot sekä viimeisimmän ottelun tiedot
    - Jos **ids_only**-parametri on 1 (oletuksena 0), palautetaan vain seurattavien pelaajien/joukkueiden tunnukset.
    - Huom! Jos seurattava pelaaja ei ole pelannut nykyisellä kaudella yhtään ottelua, ei kyseisen pelaajan osalta palauteta mitään tilastoja.
- Vaatii OAuth-allekirjoitetun pyynnön.
- Käyttäjä päätellään OAuth access tokenin perusteella - ei tarvitse tuoda parametrina.

### Lisäys käyttäjän seuraamiin pelaajiin/joukkueisiin

    POST /api/user

- Lisää käyttäjälle parametreissä määritellyn joukkueen/pelaajan seurattavaksi.
- Post-parametrina joko **team**=joukkueen_tunnus tai **pid**=pelaajan_id.
    - Jos kummatkit on määritelty, käytetään parametria **pid**.
- Paluuarvo on sama kuin vastaavassa GET-pyynnössä - lisäyksen myötä päivitettynä
  - **ids_only**-parametrin voi määritellä kuten GET-pyynnössä
- Vaatii OAuth 1.0-allekirjoitetun pyynnön.

### Poisto käyttäjän seuraamista pelaajista/joukkueista

    DELETE /api/user

- Poistaa parametreissä määritellyn pelaajan/joukkueen käyttäjän seurannasta.
- Post-parametrina joko **team**=joukkueen_tunnus tai **pid**=pelaajan_id.
    - Jos kummatkit on määritelty, käytetään parametria **pid**.
- Vaatii OAuth 1.0-allekirjoitetun pyynnön.
