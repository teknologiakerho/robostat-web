import functools
import flask

class SessionProperty:

    def __init__(self, name):
        self.name = name

    def __get__(self, obj, cls):
        try:
            return flask.session[self.name]
        except KeyError:
            return None

    def __set__(self, obj, value):
        flask.session[self.name] = value

    def __delete__(self, obj):
        flask.session.pop(self.name)

class UserSessionProxy:

    name = SessionProperty("name")
    id = SessionProperty("id")
    admin = SessionProperty("admin")

    @property
    def logged_in(self):
        return self.id is not None

    @property
    def is_admin(self):
        return self.admin is not None

    def login(self, id, name):
        self.id = id
        self.name = name

    def logout(self):
        del self.id
        del self.name

user = UserSessionProxy()

def check_login():
    user.logged_in or flask.abort(401)

def check_admin():
    user.is_admin or flask.abort(401)

def require_login(f):
    @functools.wraps(f)
    def w(*args, **kwargs):
        check_login()
        return f(*args, **kwargs)
    return w

def require_admin(f):
    @functools.wraps(f)
    def w(*args, **kwargs):
        check_admin()
        return f(*args, **kwargs)
    return w
