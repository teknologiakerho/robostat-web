import flask
import sqlalchemy as sa
from sqlalchemy.orm import selectinload, joinedload
import robostat.db as model
from robostat.util import enumerate_rank
from robostat.web.glob import db
from robostat.web.util import get_ranking, get_block
from robostat.web.views.api import default_api, jsonify, json_view

def filter_events(query, params):
    if params.get("day") == "today":
        query = query.filter(model.Event.ts_sched.between(
            sa.func.strftime("%s", "now", "start of day"),
            sa.func.strftime("%s", "now", "+1 days", "start of day")
        ))

    if "from" in params:
        query = query.filter(model.Event.ts_sched >= params.get("from", type=int))

    if "to" in params:
        query = query.filter(model.Event.ts_sched <= params.get("to", type=int))

    if "e" in params:
        query = query.filter(model.Event.id.in_(params.getlist("e", type=int)))

    if "b" in params:
        query = query.filter(model.Event.block_id.in_(params.getlist("b")))

    if "a" in params:
        query = query.filter(model.Event.arena.in_(params.getlist("a")))

    if "id" in params:
        query = query.filter(model.Event.id == params["id"])

    if params.get("sort") == "ts":
        query = query.order_by(model.Event.ts_sched)

    return query

@default_api("/teams")
@json_view
def teams():
    return list(map(jsonify, db.query(model.Team).all()))

@default_api("/judges")
@json_view
def judges():
    return list(map(jsonify, db.query(model.Judge).all()))

@default_api("/ranking/<id>")
@json_view
def ranking(id):
    ranking = get_ranking(id)
    ranking = ranking(db)

    return [{
        "rank": rank,
        "team": jsonify(team),
        "score": jsonify(score)
    } for rank, (team, score) in enumerate_rank(ranking, key=lambda x:x[1])]

@default_api("/events")
@json_view
def events():
    query = db.query(model.Event)\
            .options(
                selectinload(model.Event.teams_part)\
                .joinedload(model.EventTeam.team, innerjoin=True),
                selectinload(model.Event.judgings)\
                .joinedload(model.EventJudging.judge, innerjoin=True)
            )

    params = flask.request.values

    query = filter_events(query, params)

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
        "teams": list(map(jsonify, e.teams)),
        "judges": list(map(jsonify, e.judges))
    } for e in ret]

@default_api("/scores")
@json_view
def scores():
    query = db.query(model.Event)\
            .options(
                joinedload(model.Event.scores, innerjoin=True)
            )

    query = filter_events(query, flask.request.values)
    ret = query.all()

    return dict((e.id, [
        {
            "team_id": s.team_id,
            "judge_id": s.judge_id,
            "score": {
                "data": {}, # TODO json encoderit näille
                "desc": str(s.score_obj)
            } if s.has_score else None
        } for s in e.scores
    ]) for e in ret)
