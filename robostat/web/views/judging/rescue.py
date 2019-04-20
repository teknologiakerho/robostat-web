import quart
from robostat.rulesets.rescue import RescueRuleset, RescueResult, WEIGHTS, RescueObstacleCategory,\
        RescueMultiObstacleCategory, RescueMultiObstacleScore
from robostat.web.util import get_block, field_injector
from robostat.web.views.judging import ScoreParserError, card_renderer, scoring_renderer,\
        post_parser, autofail_key_error, check_json

cat_encoder = field_injector("__web_rescue_cat_encoder__")
cat_decoder = field_injector("__web_rescue_cat_decoder__")

@cat_encoder.of(RescueObstacleCategory)
def encode_obstacle(val):
    return str(val)

@cat_decoder.of(RescueObstacleCategory)
def decode_obstacle(val):
    try:
        return RescueResult(val["value"])
    except ValueError:
        raise ScoreParserError("Invalid result: %s" % val["value"])

@cat_encoder.of(RescueMultiObstacleCategory)
def encode_multi_obstacle(val):
    return {
        "fail": val.fail,
        "success2": val.success2,
        "success1": val.success1
    }

@cat_decoder.of(RescueMultiObstacleCategory)
def decode_multi_obstacle(val):
    try:
        vals = dict((v["value"], int(v["count"])) for v in val["values"])
    except TypeError:
        raise ScoreParserError("Invalid result: %s" % val["values"])

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
async def render_card(judging):
    return await quart.render_template("judging/event-card-rescue.html", judging=judging)

@scoring_renderer.of(RescueRuleset)
async def render_scoring(judging):
    ruleset = get_block(judging.event).ruleset

    return await quart.render_template("judging/scoring-rescue-%s.html" % str(ruleset.difficulty),
            judging=judging,
            weights=WEIGHTS,
            event_data=get_event_data(judging)
    )

@post_parser.of(RescueRuleset)
@autofail_key_error
@check_json
async def parse_post(judging, json):
    ruleset = get_block(judging.event).ruleset
    scores = json["scores"]

    ret = ruleset.create_score()

    for k,v in ret.score_categories:
        setattr(ret, k, cat_decoder[v](scores[k]))

    time = json["time"]

    try:
        t_min = int(time["min"])
        t_sec = int(time["sec"])
    except TypeError as e:
        raise ScoreParserError("Invalid time: %s" % str(e))

    # Tässä ei tarkisteta että nää olis positiivia tai että t_sec<60
    # mutta eipä se haittaa että tähän voi laittaa virheellisiä arvoja
    # koska koko score tarkistetaan myöhemmin
    ret.time = 60*t_min + t_sec

    return (judging.event.team.id, ret),
