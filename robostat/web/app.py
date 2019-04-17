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

    def __init__(self, import_name, tournament=None, **kwargs):
        super().__init__(import_name, **kwargs)
        self.register_blueprint(res)
        self.register_error_handler(UnauthorizedError, self.handle_unauth)
        self.db = None
        self.tournament = tournament or robostat.default_tournament

    def setup_login(self, admin_password=None, prefix="/auth"):
        from robostat.web.views.login import LoginView
        self.register_blueprint(
                LoginView(admin_password=admin_password).create_blueprint(),
                url_prefix=prefix
        )

    def setup_db(self, url, engine_args={},
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

def create_app(config_pyfile=None, config_envvar="ROBOSTAT_CONFIG",
        admin_password=None, tournament=None,
        init_file=None, init_envvar="ROBOSTAT_INIT",
        db_url=None, db_envvar="ROBOSTAT_DB",
        import_name=__name__):

    import os

    app = RobostatWeb(import_name)

    config_pyfile = config_pyfile or os.environ.get(config_envvar, None)

    if config_pyfile is not None:
        app.config.from_pyfile(config_pyfile)

    init = init_file or os.environ.get(init_envvar, None) or app.config.get("ROBOSTAT_INIT", None)

    if init is None:
        raise ValueError("No init file given")

    if tournament is None:
        tournament = robostat.default_tournament

    with robostat.replace_default_tournament(tournament):
        exec(open(init).read(), {})

    app.tournament = tournament

    if admin_password is None:
        admin_password = app.config.get("ROBOSTAT_ADMIN_PASSWORD", None)

    app.setup_login(admin_password)

    db_url = db_url or os.environ.get(db_envvar, None) or app.config.get("ROBOSTAT_DB", None)

    if db_url is None:
        raise ValueError("No database url given")

    app.setup_db(db_url)

    if "ROBOSTAT_LOGFILE" in app.config:
        import logging
        from robostat.web.logging import logger
        handler = logging.FileHandler(app.config["ROBOSTAT_LOGFILE"])
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    from robostat.web.views.judging import JudgingView
    from robostat.web.views.ranking import RankingView
    from robostat.web.views.timetable import TimetableView
    from robostat.web.views.api import ApiView

    judging = JudgingView().create_blueprint()
    ranking = RankingView().create_blueprint()
    timetable = TimetableView().create_blueprint()
    api = ApiView().create_blueprint()

    app.register_blueprint(judging, url_prefix="/judging")
    app.register_blueprint(ranking, url_prefix="/ranking")
    app.register_blueprint(timetable, url_prefix="/timetable")
    app.register_blueprint(api, url_prefix="/api")

    if admin_password is not None:
        from robostat.web.views.admin import AdminView
        admin = AdminView(
                api_blueprint=api,
                judging_blueprint=judging,
                ranking_blueprint=ranking
        ).create_blueprint()

        app.register_blueprint(admin, url_prefix="/admin")

    return app
