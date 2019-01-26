from time import time
from datetime import datetime
import flask
import robostat.db as model
from robostat.web.glob import db

def parse_ts(ts):
    return int(datetime.strptime(ts, "%d.%m.%Y %H:%M").timestamp())

def query_events():
    j_sub = db.query(model.EventJudging)\
            .filter(model.EventJudging.is_future==False)\
            .filter(model.EventJudging.event_id==model.Event.id)

    query = db.query(model.Event, ~j_sub.exists())\
            .join(model.Event.teams_part)\
            .join(model.EventTeam.team)

    if "b" in flask.request.values:
        blkids = flask.request.values.getlist("b")
        query = query.filter(model.Event.block_id.in_(blkids))

    if "t" in flask.request.values:
        teams = flask.request.values.getlist("t")
        query = query.filter(model.Team.name.in_(teams))

    # TODO "j" haku?

    if "from" in flask.request.values:
        if request.values["from"] == "now":
            ts_from = int(time())
        else:
            ts_from = parse_ts(request.values["from"])
        query = query.filter(model.Event.ts_sched >= ts_from)

    if "to" in flask.request.values:
        ts_to = parse_ts(request.values["to"])
        query = query.filter(model.Event.ts_sched <= ts_to)

    return query.all()

def render_timetable(event_data):
    return flask.render_template("timetable/timetable.html", event_data=event_data)

class TimetableView(flask.Blueprint):

    def __init__(self, name="timetable", import_name=__name__, **kwargs):
        super().__init__(name, import_name, **kwargs)
        self.add_url_rule("/", "index", self.index)

    def index(self):
        event_data = query_events()
        return render_timetable(event_data=event_data)
