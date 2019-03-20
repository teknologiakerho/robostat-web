import flask
from robostat.rulesets.haastattelu import HaastatteluRuleset
from robostat.web.views.judging import card_renderer, scoring_renderer, post_parser

@card_renderer.of(HaastatteluRuleset)
def render_card(judging):
    return flask.render_template("judging/event-card-haastattelu.html", judging=judging)

@scoring_renderer.of(HaastatteluRuleset)
def render_scoring(judging):
    done = (not judging.is_future) and bool(judging.score.score_obj)
    return flask.render_template("judging/scoring-haastattelu.html",
            judging=judging,
            done=done
    )

@post_parser.of(HaastatteluRuleset)
def parse_post(judging):
    return [(judging.event.team.id, bool(flask.request.json["done"]))]
