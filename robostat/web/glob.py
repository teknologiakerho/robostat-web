import flask
from werkzeug.local import LocalProxy

db = LocalProxy(lambda: flask.current_app.db)

res = flask.Blueprint("robostat", __name__,
        static_folder="static",
        static_url_path="/static/robostat",
        template_folder="templates"
)
