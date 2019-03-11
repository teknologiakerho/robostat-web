from time import time
from datetime import datetime
import flask
import sqlalchemy as sa
from sqlalchemy.orm import contains_eager
import robostat.db as model
from robostat.web.glob import db

def parse_ts(ts):
    return int(datetime.strptime(ts, "%d.%m.%Y %H:%M").timestamp())

def query_events(**kwargs):
    j_sub = db.query(model.EventJudging)\
            .filter(model.EventJudging.is_future==False)\
            .filter(model.EventJudging.event_id==model.Event.id)

    query = db.query(model.Event, ~j_sub.exists())\
            .join(model.Event.teams_part)\
            .join(model.EventTeam.team)\
            .options(
                    contains_eager(model.Event.teams_part)
                    .contains_eager(model.EventTeam.team)
            )

    if "block_ids" in kwargs:
        query = query.filter(model.Event.block_id.in_(kwargs["block_ids"]))

    if "team_names" in kwargs:
        query = query.filter(model.Team.name.in_(teams))

    if "from_ts" in kwargs:
        query = query.filter(model.Event.ts_sched >= kwargs["from_ts"])

    if "to_ts" in kwargs:
        query = query.filter(model.Event.ts_sched <= kwargs["to_ts"])

    return query.all()

def get_dates():
    query = db.query(
        sa.func.min(model.Event.ts_sched),
        sa.func.max(model.Event.ts_sched)
    ).select_from(model.Event)

    min_ts, max_ts = query.first()

def render_timetable(event_data):
    return flask.render_template("timetable/timetable.html", event_data=event_data)

class TimetableView(flask.Blueprint):

    def __init__(self, name="timetable", import_name=__name__, **kwargs):
        super().__init__(name, import_name, **kwargs)
        self.add_url_rule("/", "index", self.index)

    def index(self):
        event_data = self.get_events()

        return render_timetable(event_data=event_data)

    def get_events(self):
        flt = {}
        
        if "b" in flask.request.values:
            flt["block_ids"] = flask.request.values.getlist("b")

        if "t" in flask.request.values:
            flt["team_names"] = flask.request.values.getlist("t")

        if "from" in flask.request.values:
            flt["from_ts"] = int(time()) if request.values["from"] == "now"\
                    else parse_ts(request.values["from"])

        if "to" in flask.request.values:
            flt["to_ts"] =  parse_ts(request.values["to"])

        return query_events(**flt)
