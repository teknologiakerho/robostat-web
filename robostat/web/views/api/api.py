import flask
import functools
from robostat.web.util import field_injector

jsonifier = field_injector("__web_api_jsonifier__")

def jsonify(x):
    return jsonifier[x](x)

def json_view(f):
    @functools.wraps(f)
    def ret(*args, **kwargs):
        ret = f(*args, **kwargs)

        if isinstance(ret, tuple):
            resp = flask.jsonify(ret[0])
            resp.status_code = ret[1]
        else:
            resp = flask.jsonify(ret)

        return resp
    return ret

class ApiView(flask.Blueprint):

    _default_routes = []

    def __init__(self, name="api", import_name=__name__, **kwargs):
        super().__init__(name, import_name, **kwargs)
        self.add_url_rule("/", "index", self.index)
        self.record(self._register_defaults)

    def index(self):
        return ""

    def _register_defaults(self, state):
        for r in self._default_routes:
            r(state)

    @classmethod
    def _default_api(cls, rule, **options):
        def ret(f):
            cls._default_routes.append(lambda s: s.add_url_rule(
                rule,
                options.pop("endpoint", f.__name__),
                f,
                **options
            ))
            return f
        return ret

default_api = ApiView._default_api
