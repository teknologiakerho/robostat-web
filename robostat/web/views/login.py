import flask
import robostat.db as model
from robostat.web.glob import db
from robostat.web.login import user

class LoginView:

    def __init__(self, admin_password=None):
        self.admin_password = admin_password

    def create_blueprint(self, name="login", import_name=__name__, **kwargs):
        b = flask.Blueprint(name, import_name, **kwargs)

        b.add_url_rule("/judge", "judge", self.login, methods=["GET", "POST"])
        b.add_url_rule("/logout", "logout", self.logout, methods=["GET", "POST"])

        if self.admin_password:
            b.add_url_rule("/admin", "admin", self.admin, methods=["GET", "POST"])
            b.add_url_rule("/unadmin", "unadmin", self.unadmin, methods=["GET", "POST"])

        return b

    def login(self):
        if flask.request.method == "POST":
            try:
                key = flask.request.form["key"]
            except KeyError:
                return flask.render_template("login/judge.html", error="Puuttuva avain")

            u = db.query(model.Judge).filter_by(key=key).first()
            if u is None:
                return flask.render_template("login/judge.html", error="Tuomaria ei löytynyt")

            user.login(u.id, u.name)
            flask.flash("Olet nyt tuomari: %s" % u.name, "success")
            return flask.redirect(flask.request.args.get("return_to", "/"))

        return flask.render_template("login/judge.html")

    def admin(self):
        if flask.request.method == "POST":
            try:
                key = flask.request.form["key"]
            except KeyError:
                return flask.render_template("login/admin.html", error="Puuttuva salasana")

            if key == self.admin_password:
                user.auth_admin()
                flask.flash("Olet nyt ylläpitäjä", "success")
                return flask.redirect(flask.request.args.get("return_to", "/"))

            return flask.render_template("login/admin.html", error="Väärä salasana")

        return flask.render_template("login/admin.html")

    def logout(self):
        if user.logged_in:
            user.logout()
        return flask.redirect("/")

    def unadmin(self):
        if user.is_admin:
            user.deauth_admin()
        return flask.redirect("/")
