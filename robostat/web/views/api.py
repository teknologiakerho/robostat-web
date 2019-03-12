import flask
import functools
import sqlalchemy as sa
from sqlalchemy.orm import selectinload
import robostat.db as model
from robostat.util import enumerate_rank
from robostat.rulesets.xsumo import XSumoRank
from robostat.rulesets.rescue import RescueRank, RescueScore
from robostat.web.glob import db
from robostat.web.util import field_injector, get_ranking, get_block

jsonifier = field_injector("__web_api_jsonifier__")

@jsonifier.of(XSumoRank)
def jsonify_xsumo_rank(rank):
    return {
        "score": rank.score,
        "wins": rank.wins,
        "ties": rank.ties,
        "losses": rank.losses,
        "unplayed": rank.unplayed
    }

@jsonifier.of(RescueRank)
def jsonify_rescue_rank(rank):
    return {
        "best": jsonifier[rank.best](rank.best),
        "others": [(jsonifier[s](s) if s is not None else None) for s in rank.other_scores]
    }

@jsonifier.of(RescueScore)
def jsonify_rescue_score(score):
    return {
        "score": int(score),
        "time": score.time
    }

@jsonifier.of(model.Team)
def jsonify_team(team):
    return {
        "id": team.id,
        "name": team.name,
        "school": team.school
    }

@jsonifier.of(model.Judge)
def jsonify_judge(judge):
    return {
        "id": judge.id,
        "name": judge.name
    }

def json_view(f):
    @functools.wraps(f)
    def ret(*args, **kwargs):
        return flask.jsonify(f(*args, **kwargs))
    return ret

class ApiView(flask.Blueprint):

    def __init__(self, name="api", import_name=__name__, **kwargs):
        super().__init__(name, import_name, **kwargs)
        self.add_url_rule("/ranking/<id>", "ranking", self.ranking)
        self.add_url_rule("/events", "events", self.events)

    @json_view
    def ranking(self, id):
        ranking = get_ranking(id)
        ranking = ranking(db)

        return [{
            "rank": rank,
            "team": jsonify_team(team),
            "score": jsonifier[score](score)
        } for rank, (team, score) in enumerate_rank(ranking, key=lambda x:x[1])]

    @json_view
    def events(self):
        query = db.query(model.Event)\
                .options(
                    selectinload(model.Event.teams_part)\
                    .joinedload(model.EventTeam.team, innerjoin=True),
                    selectinload(model.Event.judgings)\
                    .joinedload(model.EventJudging.judge, innerjoin=True)
                )

        params = flask.request.values

        if params.get("day") == "today":
            query = query.filter(model.Event.ts_sched.between(
                sa.func.strftime("%s", "now", "start of day"),
                sa.func.strftime("%s", "now", "+1 days", "start of day")
            ))

        if "from" in params:
            query = query.filter(model.Event.ts_sched >= params.get("from", type=int))

        if "to" in params:
            query = query.filter(model.Event.ts_sched <= params.get("to", type=int))

        if "b" in params:
            query = query.filter(model.Event.block_id.in_(params.getlist("b")))

        if "a" in params:
            query = query.filter(model.Event.arena.in_(params.getlist("a")))

        if "id" in params:
            query = query.filter(model.Event.id == params["id"])

        if params.get("sort") == "ts":
            query = query.order_by(model.Event.ts_sched)

        if "limit" in params:
            query = query.limit(params.get("limit", type=int))

        ret = query.all()

        return [{
            "id": e.id,
            "block": {
                "id": e.block_id,
                "name": get_block(e).name
            },
            "ts_sched": e.ts_sched,
            "arena": e.arena,
            "teams": [jsonify_team(t) for t in e.teams],
            "judges": [jsonify_judge(j) for j in e.judges]
        } for e in ret]
