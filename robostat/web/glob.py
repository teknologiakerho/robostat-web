import quart
from quart.local import LocalProxy

db = LocalProxy(lambda: quart.current_app.db)
tournament = LocalProxy(lambda: quart.current_app.tournament)

res = quart.Blueprint("robostat", __name__,
        static_folder="static",
        static_url_path="/static/robostat",
        template_folder="templates"
)
