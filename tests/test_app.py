import pytest
import flask
import robostat.db as model
from robostat.web.login import user, require_login, require_admin, check_login, check_admin,\
        UnauthorizedError
from .helpers import data, as_judge, as_admin

@pytest.fixture
def app(init_app):
    @init_app.route("/no-login")
    def no_login_view():
        return "normal ok"

    @init_app.route("/require-login")
    @require_login
    def logged_in_view():
        return "login ok"

    @init_app.route("/require-admin")
    @require_admin
    def admin_view():
        return "admin ok"

    return init_app

auth_data = data(lambda: [
    model.Judge(id=1, name="Tuomari A", key="a"),
    model.Judge(id=2, name="Tuomari B", key="b")
])

def test_no_login(app, client):
    assert client.get("/no-login").data == b"normal ok"

@pytest.mark.parametrize("url,redirect", [
    ("/require-login", "/auth/judge"),
    ("/require-admin", "/auth/admin")
])
def test_login_redirects(app, client, url, redirect):
    # kirjautumisen vaativat pitäs redirectata login sivulle
    with client:
        client.get(url, follow_redirects=True)
        assert flask.request.path == redirect

@pytest.mark.parametrize("url,check", [
    ("/auth/judge", check_login),
    ("/auth/admin", check_admin)
])
@auth_data
def test_invalid_login(app, client, url, check):
    # Puuttuva avain
    with client:
        assert client.post(url).status_code == 200
        with pytest.raises(UnauthorizedError):
            check()

    with client:
        assert client.post(url, data={"key": "virheellinen-avain"}).status_code == 200
        with pytest.raises(UnauthorizedError):
            check()

@auth_data
@as_judge("a")
def test_login_judge(app, client):
    with client:
        assert client.get("/require-login").data == b"login ok"
        check_login()
        with pytest.raises(UnauthorizedError):
            check_admin()
        assert user.id == 1
        assert user.name == "Tuomari A"

@auth_data
@as_admin("password")
def test_login_admin(app, client):
    with client:
        assert client.get("/require-admin").data == b"admin ok"
        check_admin()
        with pytest.raises(UnauthorizedError):
            check_login()

@auth_data
@as_judge("a")
@as_admin("password")
def test_login_dual(app, client):
    with client:
        client.get("/no-login")
        check_login()
        check_admin()

@auth_data
@as_judge("a")
def test_logout_judge(app, client):
    with client:
        assert client.post("/auth/logout")
        with pytest.raises(UnauthorizedError):
            check_login()

@auth_data
@as_admin("password")
def test_logout_admin(app, client):
    with client:
        assert client.post("/auth/unadmin")
        with pytest.raises(UnauthorizedError):
            check_admin()
