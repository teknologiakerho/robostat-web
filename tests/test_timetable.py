import pytest
import robostat.db as model
from robostat.web.views.timetable import TimetableView
from .helpers import data

class TimetableShadows(TimetableView):
    hide_shadows = False

@pytest.fixture
def app(init_app):
    init_app.register_blueprint(
            TimetableView().create_blueprint(name="timetable"),
            url_prefix="/timetable"
    )
    init_app.register_blueprint(
            TimetableShadows().create_blueprint(name="timetableshadows"),
            url_prefix="/timetable-shadows"
    )
    return init_app

timetable_data = data(lambda: [
    model.Team(id=1, name="Sumojoukkue 1"),
    model.Team(id=2, name="Sumojoukkue 2"),
    model.Team(id=3, name="Rescue-joukkue 1"),
    model.Team(id=4, name="Rescue-joukkue 2", is_shadow=1),
    model.Judge(id=1, name="Tuomari A"),
    model.Event(
        id=1,
        block_id="xsumo.as",
        ts_sched=0,
        arena="xsumo.1",
        teams_part=[model.EventTeam(team_id=1), model.EventTeam(team_id=2)],
        judgings=[model.EventJudging(judge_id=1)]
    ),
    model.Event(
        id=2,
        block_id="rescue1.a",
        ts_sched=1,
        arena="rescue.1",
        teams_part=[model.EventTeam(team_id=3)],
        judgings=[model.EventJudging(judge_id=1)]
    ),
    model.Event(
        id=3,
        block_id="rescue1.b",
        ts_sched=2,
        arena="rescue.1",
        teams_part=[model.EventTeam(team_id=4)],
        judgings=[model.EventJudging(judge_id=1)]
    )
])

@timetable_data
def test_plain(app, client):
    resp = client.get("/timetable/")
    assert resp.status_code == 200
    assert b"Sumojoukkue 1" in resp.data
    assert b"Sumojoukkue 2" in resp.data
    assert b"Rescue-joukkue 1" in resp.data
    assert b"Rescue-joukkue 2" not in resp.data

@timetable_data
def test_good_filters(app, client):
    resp = client.get("/timetable/?t=Sumojoukkue%201")
    assert resp.status_code == 200
    assert b"Sumojoukkue 1" in resp.data
    assert b"Sumojoukkue 2" in resp.data
    assert b"Rescue-joukkue" not in resp.data

    resp = client.get("/timetable/?b=rescue1.a")
    assert resp.status_code == 200
    assert b"Sumojoukkue" not in resp.data
    assert b"Rescue-joukkue 1" in resp.data

    resp = client.get("/timetable/?day=1.1.1970")
    assert resp.status_code == 200
    assert b"Sumojoukkue" in resp.data

    resp = client.get("/timetable/?day=2.1.1970")
    assert resp.status_code == 200
    assert b"Sumojoukkue" not in resp.data

@timetable_data
def test_bad_filters(app, client):
    assert client.get("/timetable/?day=asd").status_code == 404

@timetable_data
def test_shadows(app, client):
    resp = client.get("/timetable-shadows/")
    assert b"Rescue-joukkue 2" in resp.data
