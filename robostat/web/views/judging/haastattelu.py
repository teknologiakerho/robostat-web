import quart
from robostat.rulesets.haastattelu import HaastatteluRuleset
from robostat.web.views.judging import card_renderer, scoring_renderer, post_parser,\
        autofail_key_error, check_json

@card_renderer.of(HaastatteluRuleset)
async def render_card(judging):
    return await quart.render_template("judging/event-card-haastattelu.html", judging=judging)

@scoring_renderer.of(HaastatteluRuleset)
async def render_scoring(judging):
    done = (not judging.is_future) and bool(judging.score.score_obj)
    return await quart.render_template("judging/scoring-haastattelu.html",
            judging=judging,
            done=done
    )

@post_parser.of(HaastatteluRuleset)
@autofail_key_error
@check_json
async def parse_post(judging, json):
    return [(judging.event.team.id, bool(json["done"]))]
