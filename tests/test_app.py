import flask
import robostat.db as model
from robostat.web.login import user, require_login
from .helpers import data

@data([
    model.Judge(id=1, name="Tuomari A", key="asd1"),
    model.Judge(id=2, name="Tuomari B", key="asd2")
], app_keyword="init_app")
def test_login(init_app, client):

    @init_app.route("/no-login")
    def no_login_view():
        return "nologin ok"

    @init_app.route("/require-login")
    @require_login
    def logged_in_view():
        return "login ok"

    # normaaleja viewejä pitäs pystyä näyttämään vaikka ei ole kirjautunt
    assert client.get("/no-login").data == b"nologin ok"

    # kirjautumisen vaativat pitäs redirectata login sivulle
    with client:
        client.get("/require-login", follow_redirects=True)
        assert flask.request.path == "/login"

    # virheellisillä tai puuttuvilla tunnuksilla ei pitäs pystyä kirjautumaan
    with client:
        assert client.post("/login").status_code == 200
        assert not user.logged_in

    with client:
        assert client.post("/login", data={"key": "virheellinen-avain"}).status_code == 200
        assert not user.logged_in

    # Nyt pitäs onnistua
    with client:
        client.post("/login", data={"key": "asd1"})
        assert user.logged_in
        assert user.id == 1
        assert user.name == "Tuomari A"

    assert client.get("/require-login").data == b"login ok"

    # Uloskirjautuminen myös
    with client:
        assert client.post("/logout")
        assert not user.logged_in
