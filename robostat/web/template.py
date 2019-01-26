import flask
from datetime import datetime
from robostat.util import enumerate_rank
from robostat.web.glob import res
from robostat.web.util import get_block
from robostat.web.login import user

res.add_app_template_global(user, "user")
res.add_app_template_global(get_block)

res.add_app_template_filter(enumerate_rank)

@res.app_template_filter()
def enumerate_ranking(ranking):
    return enumerate_rank(ranking, key=lambda x: x[1])

@res.app_template_filter()
def team_card(team):
    return flask.render_template("team-card.html", team=team)

@res.app_template_filter()
def localdate(x, fmt="%-d.%-m.%Y %H:%M"):
    return datetime.fromtimestamp(x).astimezone(tz=None).strftime(fmt)
