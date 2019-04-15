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

class LoginHandler:

    def __init__(self, login_url, logout_url):
        self.login_url = login_url
        self.logout_url = logout_url

    def login(self, client, key):
        return client.post(self.login_url, data={"key": key})

    def logout(self, client):
        return client.post(self.logout_url)

    @contextlib.contextmanager
    def session(self, client, key):
        self.login(client, key)
        try:
            yield
        finally:
            self.logout(client)

    def as_auth(self, key, client_keyword="client"):
        def ret(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                with self.session(kwargs[client_keyword], key):
                    return f(*args, **kwargs)
            return wrapper
        return ret

judge_handler = LoginHandler("/auth/judge", "/auth/logout")
admin_handler = LoginHandler("/auth/admin", "/auth/unadmin")
as_judge = judge_handler.as_auth
as_admin = admin_handler.as_auth
