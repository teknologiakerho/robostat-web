import pytest
import robostat.db as model
from robostat.rulesets.rescue import RescueRuleset, RescueObstacleCategory,\
        RescueMultiObstacleCategory
from robostat.web.views.judging import JudgingView
from robostat.web.views.judging.xsumo import parse_post_xs
from robostat.web.views.judging.rescue import parse_post as parse_post_r
from .helpers import data, as_judge, as_admin

@pytest.fixture
def app(init_app):
    init_app.register_blueprint(JudgingView().create_blueprint(), url_prefix="/judging")
    return init_app

def XS(t1, t2, *rounds):
    return {
        "team1": t1,
        "team2": t2,
        "rounds": rounds
    }

def XSsym(t1, t2, *rounds):
    json = XS(t1, t2, *rounds)
    json2 = dict(json.items())

    for r in json2["rounds"]:
        for k,v in r.items():
            if v == 0:
                r[k] = 1
            elif v == 1:
                r[k] = 0

    return json, json2

def R1(values):
    cats = RescueRuleset.by_difficulty(1).create_score().score_categories
    scores = {}

    for k,v in cats:
        if isinstance(v, RescueObstacleCategory):
            val = values.get(k, "F")
            scores[k] = {"value": val}
        else:
            val = values.get(k, (0, 0, 0))
            scores[k] = {"values": [
                {
                    "value": "success1",
                    "count": val[0]
                },
                {
                    "value": "success2",
                    "count": val[1]
                },
                {
                    "value": "fail",
                    "count": val[2]
                }
            ]}

    time = {}
    time["min"], time["sec"] = values.get("time", (0, 0))

    return {"scores": scores, "time": time}

xsumo_single_data = data(lambda: [
    model.Team(id=1, name="Sumojoukkue 1"),
    model.Team(id=2, name="Sumojoukkue 2"),
    model.Judge(id=1, name="Sumotuomari A", key="a"),
    model.Event(
        id=1,
        block_id="xsumo.as",
        ts_sched=0,
        arena="xsumo.1",
        teams_part=[model.EventTeam(team_id=1), model.EventTeam(team_id=2)],
        judgings=[model.EventJudging(judge_id=1)]
    )
])

rescue_data = data(lambda: [
    model.Team(id=1, name="Rescuejoukkue 1"),
    model.Judge(id=1, name="Tuomari A", key="a"),
    model.Judge(id=2, name="Tuomari B", key="b"),
    model.Event(
        id=1,
        block_id="rescue1.a",
        ts_sched=0,
        arena="rescue.1",
        teams_part=[model.EventTeam(team_id=1)],
        judgings=[model.EventJudging(judge_id=1)]
    ),
    model.Event(
        id=2,
        block_id="rescue1.b",
        ts_sched=1,
        arena="rescue.1",
        teams_part=[model.EventTeam(team_id=1)],
        judgings=[model.EventJudging(judge_id=2)]
    )
])

@rescue_data
@as_judge("a")
def test_auth(app, client):
    assert client.get("/judging/scoring/1").status_code == 200
    assert client.get("/judging/scoring/2").status_code == 404

@rescue_data
@as_admin("password")
def test_as_judge(app, client):
    assert client.get("/judging/scoring/1?as=1").status_code == 200
    assert client.get("/judging/scoring/2?as=1").status_code == 404

def check_xsumo_parsed_scores(json, s1, s2):
    assert len(s1.rounds) == len(json["rounds"])
    assert len(s2.rounds) == len(json["rounds"])

    for rj, r1, r2 in zip(json["rounds"], s1.rounds, s2.rounds):
        if "first" in rj:
            assert rj["first"] == (0 if r1.first else 1)
        else:
            assert (not r1.first) and (not r2.first)

        sr1, sr2 = str(r1.result), str(r2.result)

        if "result" in rj:
            results = {"tie": ("T", "T"), 0: ("W", "L"), 1: ("L", "W")}
            assert (sr1, sr2) == results[rj["result"]]
        else:
            assert (sr1, sr2) == ("L", "L")

# TODO: tässä vois generoida kaikki vaihtoehdot samalla tavalla kun coren testeissä
@pytest.mark.parametrize("json", [
    XS(1, 2),
    *XSsym(1, 2, {"first": 0}),
    *XSsym(1, 2, {"first": 0, "result": "tie"}),
    *XSsym(1, 2, {"first": 0, "result": 0}),
    *XSsym(1, 2, {"first": 0, "result": 1}),
    *XSsym(1, 2, {"first": 0}, {"first": 1}),
    *XSsym(1, 2, {"first": 0}, {"first": 0, "result": "tie"}),
    *XSsym(1, 2, {"first": 0, "result": 1}, {"first": 0, "result": 0})
])
@xsumo_single_data
@as_judge("a")
def test_xsumo_valid_request(app, client, json):
    with client:
        assert client.post("/judging/scoring/1", json=json).status_code == 200
        judging = app.db.query(model.EventJudging).filter_by(event_id=1, judge_id=1).first()
        (t1, s1), (t2, s2) = parse_post_xs(judging)

    assert (t1, t2) == (1, 2)
    check_xsumo_parsed_scores(json, s1, s2)

@pytest.mark.parametrize("json", [
    # Puuttuva data
    None, {},

    # Puuttuva joukkue
    {"team1": 1, "rounds": [] },

    # Virheellinen joukkue
    XS(1, 100),

    # Virheelliset kierrokset
    XS(1, 2, {"first": -1}),
    XS(1, 2, {"first": "asd"}),
    XS(1, 2, {"first": 1, "result": "asd"}),
    XS(1, 2, {"result": "tie"})
])
@xsumo_single_data
@as_judge("a")
def test_xsumo_invalid_request(app, client, json):
    assert client.post("/judging/scoring/1", json=json).status_code == 400

@pytest.mark.parametrize("json,score,time", [
    (R1({}), 0, 0),
    (R1({"viiva_punainen": "S"}), 20, 0),
    (R1({"viiva_punainen": "H", "time": (1, 20)}), 10, 80),
    (R1({"viiva_palat": (2, 1, 0), "time": (0, 30)}), 25, 30),
    (R1({"viiva_punainen": "S", "viiva_palat": (1, 2, 3), "time": (10, 0)}), 40, 600)
])
@rescue_data
@as_judge("a")
def test_rescue_valid_request(app, client, json, score, time):
    with client:
        assert client.post("/judging/scoring/1", json=json).status_code == 200
        judging = app.db.query(model.EventJudging).filter_by(event_id=1, judge_id=1).first()
        (_, s), = parse_post_r(judging)

    assert int(s) == score
    assert s.time == time

@pytest.mark.parametrize("json", [
    # Puuttuva data
    None, {},

    # Puuttuva aika
    R1({"time": (None, None)}),
    R1({"time": (1, None)}),
    R1({"time": (None, 1)}),

    # Puuttuvat pisteet
    R1({"viiva_punainen": None}),
    R1({"viiva_palat": (1, 2, None)}),
])
@rescue_data
@as_judge("a")
def test_xsumo_invalid_request(app, client, json):
    assert client.post("/judging/scoring/1", json=json).status_code == 400

@rescue_data
@as_judge("a")
def test_xsumo_invalid_request2(app, client):
    # Puuttuva kategoria
    json = R1({})
    del json["scores"]["viiva_punainen"]
    assert client.post("/judging/scoring/1", json=json).status_code == 400

@xsumo_single_data
@as_judge("a")
def test_past_future(app, client):
    assert b"/judging/scoring/1" in client.get("/judging/list/future").data
    assert b"/judging/scoring/1" not in client.get("/judging/list/past").data

    client.post("/judging/scoring/1", json=XS(1,2))

    assert b"/judging/scoring/1" not in client.get("/judging/list/future").data
    assert b"/judging/scoring/1" in client.get("/judging/list/past").data
