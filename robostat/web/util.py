import inspect
import quart
from robostat.web.glob import tournament

def get_block(event):
    return event.get_block(tournament=tournament)

def decode_score(score):
    if not score.has_score:
        return None

    ruleset = get_block(score.event).ruleset
    return ruleset.decode(score.data)

def hide(f):
    f.__web_hidden__ = True
    return f

def is_hidden(f):
    return hasattr(f, "__web_hidden__")

def get_ranking(id):
    try:
        ret = tournament.rankings[id]
    except KeyError:
        quart.abort(404)

    if is_hidden(ret):
        quart.abort(404)

    return ret

class field_injector:

    def __init__(self, field):
        self.field = field

    def set(self, cls, f):
        # XXX: python automatically binds methods owned by class when you getattr() then
        # so this is to get around that
        if callable(f) and inspect.isclass(cls):
            f = staticmethod(f)
        setattr(cls, self.field, f)

    def get(self, instance, default=None):
        return getattr(instance, self.field, default)

    def of(self, cls):
        def ret(f):
            self.set(cls, f)
            return f
        return ret

    def __call__(self, f):
        def ret(cls):
            self.set(cls, f)
            return cls
        return ret

    def __getitem__(self, key):
        return getattr(key, self.field)

    def __contains__(self, key):
        return hasattr(key, self.field)
