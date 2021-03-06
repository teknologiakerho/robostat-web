from time import time
from datetime import datetime
import flask
import sqlalchemy as sa
from sqlalchemy.orm import subqueryload
import robostat.db as model
from robostat.tournament import hide_query_shadows
from robostat.ruleset import Ruleset
from robostat.web.glob import db
from robostat.web.util import field_injector

event_renderer = field_injector("__web_timetable_event_renderer__")

@event_renderer.of(Ruleset)
def render_default_event(event):
    return flask.render_template("timetable/event.html", event=event)

def parse_date(ts):
    return int(datetime.strptime(ts, "%d.%m.%Y").timestamp())

def query_events(**kwargs):
    #j_sub = db.query(model.EventJudging)\
    #        .filter(model.EventJudging.is_future==False)\
    #        .filter(model.EventJudging.event_id==model.Event.id)

    #query = db.query(model.Event, ~j_sub.exists())\
    #        .join(model.Event.teams_part)\
    #        .join(model.EventTeam.team)\
    #        .options(
    #                contains_eager(model.Event.teams_part)
    #                .contains_eager(model.EventTeam.team)
    #        )

    query = db.query(model.Event)\
            .options(
                    subqueryload(model.Event.teams_part)
                    .joinedload(model.EventTeam.team, innerjoin=True)
            )

    if kwargs.get("hide_shadows"):
        query = hide_query_shadows(query)

    if "block_ids" in kwargs:
        query = query.filter(model.Event.block_id.in_(kwargs["block_ids"]))

    if "arenas" in kwargs:
        query = query.filter(model.Event.arena.in_(kwargs["arenas"]))

    if "team_names" in kwargs:
        #query = query.filter(model.Team.name.in_(kwargs["team_names"]))
        query = query.join(model.Event.teams_part)\
                .join(model.EventTeam.team)\
                .filter(model.Team.name.in_(kwargs["team_names"]))

    if "intervals" in kwargs:
        query = query.filter(sa.or_(model.Event.ts_sched.between(start, end)\
                for start, end in kwargs["intervals"]))

    return query.all()

def get_dates():
    query = db.query(
        sa.func.min(model.Event.ts_sched),
        sa.func.max(model.Event.ts_sched)
    ).select_from(model.Event)

    min_ts, max_ts = query.first()

class TimetableView:

    hide_shadows = True

    def create_blueprint(self, name="timetable", import_name=__name__, **kwargs):
        b = flask.Blueprint(name, import_name, **kwargs)
        b.add_url_rule("/", "index", self.index, methods=("GET", "POST"))
        b.add_url_rule("/search", "search", self.search)
        return b

    def index(self):
        flt = self.get_filter()
        event_data = query_events(**flt, hide_shadows=self.hide_shadows)
        return flask.render_template("timetable/timetable.html",
                event_data=event_data,
                event_filter=flt,
                render_event=self.render_event
        )

    def search(self):
        teams = self.get_teams()
        days = db.query(sa.func.strftime(
            "%s",
            model.Event.ts_sched,
            "unixepoch",
            "localtime",
            "start of day"
        )).distinct().all()
        tournament = flask.current_app.tournament
        return flask.render_template("timetable/search.html",
                teams=teams,
                days=[int(day) for (day,) in days],
                blocks=tournament.blocks.values()
        )

    def get_filter(self):
        flt = {}
        
        if "b" in flask.request.values:
            flt["block_ids"] = flask.request.values.getlist("b")

        if "a" in flask.request.values:
            flt["arenas"] = flask.request.values.getlist("a")

        if "t" in flask.request.values:
            flt["team_names"] = flask.request.values.getlist("t")

        if "day" in flask.request.values:
            try:
                flt["intervals"] = [(ts,ts+60*60*24) for ts in\
                        map(parse_date, flask.request.values.getlist("day"))]
            except ValueError:
                flask.abort(404)

        return flt

    def get_teams(self):
        query = db.query(model.Team)\
                .order_by(model.Team.name)

        if self.hide_shadows:
            query = query.filter_by(is_shadow=False)

        return query.all()

    def render_event(self, event):
        tournament = flask.current_app.tournament
        if event.block_id in tournament.blocks:
            ruleset = event.get_block(tournament).ruleset
            return event_renderer[ruleset](event=event)

        return render_default_event(event=event)
