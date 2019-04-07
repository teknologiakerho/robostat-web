import flask
import sqlalchemy as sa
from sqlalchemy.orm import scoped_session, sessionmaker
import robostat
import robostat.web.db
import robostat.web.template
from robostat.web.logging import logger
from robostat.web.glob import res
from robostat.web.login import UnauthorizedError

class RobostatWeb(flask.Flask):

    def __init__(self, import_name, tournament=None, admin_password=None, **kwargs):
        super().__init__(import_name, **kwargs)
        self.register_blueprint(res)
        self.register_blueprint(self.create_login_blueprint(admin_password), url_prefix="/auth")
        self.register_error_handler(UnauthorizedError, self.handle_unauth)
        self.db = None
        self.tournament = tournament or robostat.default_tournament

    def create_login_blueprint(self, admin_password):
        from robostat.web.views.login import LoginView
        return LoginView(admin_password=admin_password)

    def configure_db(self, url, engine_args={},
            session_args={"autocommit": False, "autoflush": False}):

        logger.debug("Connecting db: %s %s" % (url, str(engine_args)))
        engine = sa.create_engine(url, **engine_args)
        self.db = scoped_session(sessionmaker(bind=engine, **session_args))

        @self.teardown_appcontext
        def remove_session(_):
            self.db.remove()

    def handle_unauth(self, error):
        redir = error.need_admin and "login.admin" or "login.judge"
        return flask.redirect("%s?return_to=%s" % (
            flask.url_for(redir),
            flask.request.url
        ))
