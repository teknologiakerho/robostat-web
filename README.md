Robostat-web
============

Web-käyttöliittymä [robostatille][1]

  [1]: https://github.com/teknologiakerho/robostat-core

Ominaisuudet
------------

 - Tuomarointi (tunnistautuminen tuomarikohtaisella avaimella)
 - Aikataulut
 - Sijoitukset
 - HTTP api
 - Ylläpitonäkymä

Kaikki sivut ovat muokattavia lajikohtaisesti.

Käyttö
------

Testikäyttöön tai yksinkertaisiin tilanteisiin voit käyttää suoraan `robostat.web.app`-moduulia.
Jos esimerkiksi konfiguraatiotiedostosi on nimeltään `config.py`, niin voit tehdä
seuraavalla tavalla.

```shell
export FLASK_APP=robostat.web.app
export ROBOSTAT_CONFIG=config.py
flask run
```

Vakavampaan käyttöön voit lempi-WSGI-palvelintasi. Esimerkiksi nginx+uWSGI kombo toimii hyvin.

Jos tarvitset monimutkaisempia virityksiä, voit kutsua suoraan `robostat.web.app.create_app`-funktiota tai luoda itsellesi `robostat.web.app.RobostatWeb`-instanssin ja käyttää paketin `robostat.web.views` komponentteja tarpeesi mukaan.

Lisenssi
--------
Robostat on julkaistu MIT-lisenssillä.
