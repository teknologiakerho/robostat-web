import functools
import quart
from robostat.web.util import field_injector

jsonifier = field_injector("__web_api_jsonifier__")

def jsonify(x):
    return jsonifier[x](x)

def json_view(f):
    @functools.wraps(f)
    async def ret(*args, **kwargs):
        ret = await f(*args, **kwargs)

        if isinstance(ret, tuple):
            resp = quart.jsonify(ret[0])
            resp.status_code = ret[1]
        else:
            resp = quart.jsonify(ret)

        return resp
    return ret

class ApiError(Exception):

    def __init__(self, mes, code=400):
        super().__init__(mes)
        self.code = code

class ApiView:

    _default_routes = []

    def create_blueprint(self, name="api", import_name=__name__, **kwargs):
        b = quart.Blueprint(name, import_name, **kwargs)
        b.register_error_handler(ApiError, self.handle_api_error)
        b.add_url_rule("/", "index", self.index)
        b.record(self._register_defaults)
        return b

    async def index(self):
        return ""

    def handle_api_error(self, e):
        return quart.jsonify(error=str(e)), e.code

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
