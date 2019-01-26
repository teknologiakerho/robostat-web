import flask
import robostat.db as model
from robostat.web.glob import db
from robostat.web.login import user

class LoginView(flask.Blueprint):

    def __init__(self, name="login", import_name=__name__, **kwargs):
        super().__init__(name, import_name, **kwargs)
        self.add_url_rule("/login", "login", self.login, methods=["GET", "POST"])
        self.add_url_rule("/logout", "logout", self.logout, methods=["GET", "POST"])

    def login(self):
        if flask.request.method == "POST":
            try:
                key = flask.request.form["key"]
            except KeyError:
                return flask.render_template("login.html", error="Puuttuva avain")

            u = db.query(model.Judge).filter_by(key=key).first()
            if u is None:
                return flask.render_template("login.html", error="Käyttäjää ei löytynyt")

            user.login(u.id, u.name)
            return flask.redirect(flask.request.args.get("return_to", "/"))

        return flask.render_template("login.html")

    def logout(self):
        user.logout()
        return flask.redirect("/")
