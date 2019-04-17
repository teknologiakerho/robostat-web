import os
import sys
import collections
import logging
import flask
import sqlalchemy as sa
from sqlalchemy.orm import joinedload
import robostat.db as model
from robostat.util import lazy
from robostat.web.glob import db
from robostat.web.login import check_admin

class AdminView:

    def __init__(self, api_blueprint, judging_blueprint=None, ranking_blueprint=None):
        self._api_prefix = api_blueprint.name
        self._judging_prefix = judging_blueprint.name if judging_blueprint is not None else None
        self._ranking_prefix = ranking_blueprint.name if ranking_blueprint is not None else None

    def create_blueprint(self, name="admin", import_name=__name__, **kwargs):
        b = flask.Blueprint(name, import_name, **kwargs)
        b.before_request(check_admin)
        b.add_url_rule("/", "index", self.index)
        b.add_url_rule("/dashboard", "dashboard", self.dashboard)
        b.add_url_rule("/database", "database", self.database)
        b.add_url_rule("/timetables", "timetables", self.timetables)
        b.add_url_rule("/debug", "debug", self.debug)
        b.add_url_rule("/block/<id>", "block", self.block)
        return b

    def index(self):
        return flask.redirect(flask.url_for(".dashboard"))

    def dashboard(self):
        return flask.render_template("admin/dashboard.html",
                blocks=self.get_blocks(),
                rankings=self.get_rankings(),
                ranking_endpoint=self.ranking_endpoint()
        )

    def database(self):
        return flask.render_template("admin/database.html",
                api=self.api_endpoint("index")
        )

    def timetables(self):
        return flask.render_template("admin/timetables.html")

    def debug(self):
        return flask.render_template("admin/debug.html", debug=self.get_debug())

    def block(self, id):
        return flask.render_template("admin/block.html",
                api=self.api_endpoint("index"),
                block=self.get_block(id),
                scoring_endpoint=self.scoring_endpoint()
        )

    def scoring_endpoint(self):
        if self._judging_prefix is None:
            return None
        return "%s.scoring_root" % self._judging_prefix

    def ranking_endpoint(self):
        if self._ranking_prefix is None:
            return None
        return "%s.ranking" % self._ranking_prefix

    def api_endpoint(self, name):
        return "%s.%s" % (self._api_prefix, name)

    def get_blocks(self):
        tournament = flask.current_app.tournament

        ret = collections.defaultdict(dict)

        judging_counts = db.query(
                model.Event.block_id,
                sa.func.count(model.EventJudging.ts),
                sa.func.count()
            )\
            .select_from(model.Event)\
            .join(model.Event.judgings)\
            .group_by(model.Event.block_id)\
            .all()

        for id, j, j_max in judging_counts:
            ret[id].update({"j": j, "j_max": j_max})

        for id, block in tournament.blocks.items():
            ret[id].update({"block": block})

        return ret.items()

    def get_rankings(self):
        tournament = flask.current_app.tournament
        return tournament.rankings.items()

    def get_last_judgings(self, limit):
        return db.query(model.EventJudging)\
                .filter(~model.EventJudging.is_future)\
                .order_by(model.EventJudging.ts.desc())\
                .limit(limit)\
                .options(
                    joinedload(model.EventJudging.event, innerjoin=True)
                    .joinedload(model.Event.teams_part, innerjoin=True)
                    .joinedload(model.EventTeam.team, innerjoin=True)
                )\
                .all()

    def get_debug(self):
        return [
            ("Python", sys.version),
            ("Flask", flask.__version__),
            ("Polku", os.getcwd()),
            ("Tietokanta", db.get_bind().url),
            ("Lokitaso (robostat)", logging.getLogger("robostat").getEffectiveLevel()),
            ("Lokitaso (robostat.web)", logging.getLogger("robostat.web").getEffectiveLevel())
        ]

    def get_block(self, id):
        tournament = flask.current_app.tournament
        return tournament.blocks.get(id) or flask.abort(404)
