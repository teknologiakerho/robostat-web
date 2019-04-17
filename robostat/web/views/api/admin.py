import functools
import flask
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
import robostat.db as model
from robostat.web.glob import db
from robostat.web.login import check_admin, UnauthorizedError
from robostat.web.logging import request_logger
from robostat.web.views.api import ApiError, default_api, jsonify, json_view

def auto_key_error(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KeyError as e:
            raise ApiError("Missing field: %s" % str(e))
    return wrapper

def require_admin(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            check_admin()
        except UnauthorizedError:
            raise ApiError("You need admin", code=401)
        return f(*args, **kwargs)
    return wrapper

def require_json(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        json = flask.request.json
        if json is None:
            raise ApiError("You need json")
        return f(*args, **kwargs, json=json)
    return wrapper

def jsonify_event(e):
    return {
        "id": e.id,
        "teams": [t.team_id for t in e.teams_part],
        "judges": [j.judge_id for j in e.judgings],
        "arena": e.arena,
        "ts_sched": e.ts_sched
    }

def commit():
    try:
        db.commit()
    except IntegrityError as e:
        raise ApiError(str(e))

def parse_team(team, json):
    team.name = json.get("name", team.name)
    team.school = json.get("school", team.school)
    team.is_shadow = bool(json.get("shadow", team.is_shadow))
    return team

def parse_judge(judge, json):
    judge.name = json.get("name", judge.name)
    judge.key = json.get("key", judge.key)
    return judge

admin_api = lambda f: json_view(require_json(require_admin(auto_key_error(f))))

@default_api("/events/update", methods=["POST"])
@admin_api
def update_event(json):
    try:
        event_data = dict((int(eid), {
            "teams": set(map(int, ev["teams"])),
            "judges": set(map(int, ev["judges"])),
            "arena": ev["arena"],
            "ts_sched": int(ev["ts_sched"])
        }) for eid,ev in json.items())
    except (TypeError, ValueError):
        raise ApiError("Invalid event data")

    query = db.query(model.Event)\
            .filter(model.Event.id.in_(event_data))\
            .options(
                joinedload(model.Event.teams_part),
                joinedload(model.Event.judgings)
            )

    events = query.all()

    update_part = [e for e in events if\
            set(t.team_id for t in e.teams_part) != event_data[e.id]["teams"]]

    # Tää täytyy tehdä kahdessa osassa koska flush() kutsu välissä
    # ajaa triggerit jotka poistaa vanhat scoret
    if update_part:
        for e in update_part:
            request_logger.info("Updating participation on event %d (%s -> %s)" %\
                    (e.id, set(t.team_id for t in e.teams_part), event_data[e.id]["teams"]))

        for e in update_part:
            for t in e.teams_part:
                db.delete(t)

        db.flush()

        db.add_all([model.EventTeam(
            event_id=e.id,
            team_id=tid
        ) for tid in event_data[e.id]["teams"] for e in update_part])

    # Tuomaroinneille vanhoja scoreja ei poisteta
    # Tän silmukan jälkeen e_datassa on jäljellä vaan uudet judget
    for e in events:
        e_data = event_data[e.id]
        for j in e.judgings:
            if j.judge_id in e_data["judges"]:
                e_data["judges"].remove(j.judge_id)
            else:
                request_logger.info("Removing judge %d from event %d" % (j.judge_id, e.id))
                db.delete(j)

    for e in events:
        if event_data[e.id]["judges"]:
            request_logger.info("Adding judges: %s to event %d" % (event_data[e.id]["judges"],e.id))

    db.add_all([model.EventJudging(
        event_id=e.id,
        judge_id=jid
    ) for jid in event_data[e.id]["judges"] for e in events])

    # Lopuks loput tiedot
    for e in events:
        e_data = event_data[e.id]
        e.arena = e_data["arena"]
        e.ts_sched = e_data["ts_sched"]

    try:
        commit()
    except:
        request_logger.exception("Failed to commit event update")
        raise

    # Hae uudestaan yhdellä kyselyllä, muuten sqlalchemy hakee jokaisen erikseen
    return dict((e.id, jsonify_event(e)) for e in query.all())

@default_api("/events/create", methods=["POST"])
@admin_api
def create_event(json):
    try:
        event = model.Event(
            arena=json["arena"],
            ts_sched=int(json["ts_sched"]),
            block_id=json["block_id"],
            teams_part=[model.EventTeam(team_id=int(t)) for t in json["teams"]],
            judgings=[model.EventJudging(judge_id=int(j)) for j in json["judges"]]
        )
    except (TypeError, ValueError):
        raise ApiError("Invalid event data")

    db.add(event)
    commit()

    return jsonify_event(event)

@default_api("/events/<id>/delete", methods=["POST"])
@json_view
@require_admin
def delete_event(id):
    try:
        db.query(model.Event).filter_by(id=id).delete()
        commit()
    except:
        request_logger.exception("Failed to delete event (id=%d)" % id)
        raise

    return {"status": "OK"}

@default_api("/teams/<id>/update", methods=["POST"])
@admin_api
def update_team(id, json):
    team = db.query(model.Team).filter_by(id=id).first()

    if team is None:
        raise ApiError("Team doesn't exist", code=404)

    parse_team(team, json)
    commit()

    return {**jsonify(team), "shadow": bool(team.is_shadow)}

@default_api("/teams/create", methods=["POST"])
@admin_api
def create_team(json):
    team = parse_team(model.Team(), json)
    db.add(team)
    commit()
    
    return {**jsonify(team), "shadow": bool(team.is_shadow)}

@default_api("/teams/<id>/delete", methods=["POST"])
@json_view
@require_admin
def delete_team(id):
    team = db.query(model.Team).filter_by(id=id).first()

    if team is None:
        raise ApiError("Team doesn't exist", code=404)

    db.delete(team)
    commit()

    return {"status": "OK"}

@default_api("/judges/<id>/update", methods=["POST"])
@admin_api
def update_judge(id, json):
    judge = db.query(model.Judge).filter_by(id=id).first()

    if judge is None:
        raise ApiError("Judge doesn't exist", code=404)

    parse_judge(judge, json)
    commit()

    return {**jsonify(judge), "key": judge.key}

@default_api("/judges/create", methods=["POST"])
@admin_api
def create_judge(json):
    judge = parse_judge(model.Judge(), json)
    db.add(judge)
    commit()

    return {**jsonify(judge), "key": judge.key}

@default_api("/judges/<id>/delete", methods=["POST"])
@json_view
@require_admin
def delete_judge(id):
    judge = db.query(model.Judge).filter_by(id=id).first()

    if judge is None:
        raise ApiError("Judge doesn't exist", code=404)

    db.delete(judge)
    commit()

    return {"status": "OK"}
