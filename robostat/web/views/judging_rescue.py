import flask
from robostat.rulesets.rescue import RescueRuleset, WEIGHTS, RescueObstacleCategory,\
        RescueMultiObstacleCategory, RescueMultiObstacleScore, FAIL, SUCCESS_1, SUCCESS_2
from robostat.web.util import get_block, field_injector
from robostat.web.views.judging import card_renderer, scoring_renderer, post_parser

cat_encoder = field_injector("__web_rescue_cat_encoder__")
cat_decoder = field_injector("__web_rescue_cat_decoder__")

@cat_encoder.of(RescueObstacleCategory)
def encode_obstacle(val):
    return ["fail", "success2", "success1"][val]

@cat_decoder.of(RescueObstacleCategory)
def decode_obstacle(val):
    return {
        "fail": FAIL,
        "success2": SUCCESS_2,
        "success1": SUCCESS_1
    }[val["value"]]

@cat_encoder.of(RescueMultiObstacleCategory)
def encode_multi_obstacle(val):
    return {
        "fail": val.fail,
        "success2": val.success2,
        "success1": val.success1
    }

@cat_decoder.of(RescueMultiObstacleCategory)
def decode_multi_obstacle(val):
    vals = dict((v["value"], v["count"]) for v in val["values"])
    return RescueMultiObstacleScore(**vals)

def get_event_data(judging):
    if judging.is_future:
        return None

    ret = {}
    
    score = judging.score.score_obj
    for k,v in score.__cats__:
        val = getattr(score, k)
        if v in cat_encoder:
            val = cat_encoder[v](val)
        ret[k] = val

    return ret

@card_renderer.of(RescueRuleset)
def render_card(judging):
    return flask.render_template("judging/event-card-rescue.html", judging=judging)

@scoring_renderer.of(RescueRuleset)
def render_scoring(judging):
    ruleset = get_block(judging.event).ruleset

    return flask.render_template("judging/scoring-rescue-%s.html" % str(ruleset.difficulty),
            judging=judging,
            weights=WEIGHTS,
            event_data=get_event_data(judging)
    )

@post_parser.of(RescueRuleset)
def parse_post(judging):
    ruleset = get_block(judging.event).ruleset
    json = flask.request.json
    scores = json["scores"]

    ret = ruleset.create_score()

    for k,v in ret.__cats__:
        if k != "time":
            setattr(ret, k, cat_decoder[v](scores[k]))

    time = json["time"]
    ret.time = 60*time["min"] + time["sec"]

    return [(judging.event.team.id, ret), ]
