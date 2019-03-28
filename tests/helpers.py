import os
import functools
import contextlib
from sqlalchemy.orm.session import make_transient
import robostat.db as model
from pttt.timetable import parse_timetable

def get_or_insert(db, cls, names):
    ret = db.query(cls).filter(cls.name.in_(names)).all()
    if len(ret) < len(names):
        add = [cls(name=name) for name in set(names).difference(x.name for x in ret)]
        db.add_all(add)
        db.commit()
        ret.extend(add)
    return ret

def make_events(db, block, timetable, j=1):
    # XXX tää melko sama koodi on rsx:ssä joten sen vois ottaa erilleen
    k = len(timetable[0]) - j - 1
    teams = set(timetable[:,1:1+k].labels)
    judges = set(timetable[:,1+k:].labels)

    teams = get_or_insert(db, model.Team, teams)
    judges = get_or_insret(db, model.Judge, judges)

    teams = dict((t.name, t) for t in teams)
    judges = dict((j.name, j) for j in judges)

    return [model.Event(
        block_id=block,
        ts_sched=int(e.time),
        arena=e[0].name,
        teams_part=[model.EventTeam(team_id=teams[l.name].id) for l in e[1:1+k]],
        judgings=[model.EventJudging(judge_id=judges[l.name].id) for l in e[1+k:]]
    )]

def import_(block, tsvname, *, j=1, app_keyword="app"):
    def ret(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            timetable = parse_timetable(open(tsv).read(), datefmt="%d.%m.%Y %H:%M")
            db = kwargs[app_keyword].db
            events = make_events(db, block, timetable, j=j)
            db.add_all(events)
            db.commit()
            return f(*args, **kwargs)
        return wrapper
    return ret

def data(d, app_keyword="app"):
    def ret(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            db = kwargs[app_keyword].db
            if callable(d):
                objs = d()
            else:
                objs = d
            db.add_all(objs)
            db.commit()

            return f(*args, **kwargs)
        return wrapper
    return ret

def login(client, key):
    return client.post("/login", data={"key": key})

def logout(client):
    return client.post("/logout")

@contextlib.contextmanager
def user_session(client, key):
    login(client, key)
    try:
        yield
    finally:
        logout(client)

def as_user(key, client_keyword="client"):
    def ret(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            with user_session(kwargs[client_keyword], key):
                return f(*args, **kwargs)
        return wrapper
    return ret
