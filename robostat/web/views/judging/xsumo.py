import quart
from robostat.rulesets.xsumo import XSumoRuleset, XSumoResult, XSRuleset, XSRoundScore,\
        calc_results
from robostat.web.util import get_block
from robostat.web.views.judging import ScoreParserError, card_renderer, scoring_renderer,\
        post_parser, autofail_key_error, check_json

def get_event_data_xs(judging):
    ret = {}

    scores = sorted(judging.scores, key=lambda x: x.team.name)

    ret["teams"] = [{
        "id": s.team.id,
        "name": s.team.name
    } for s in scores]

    if not judging.is_future:
        ret["rounds"] = [{
            "first": 0 if r1.first else (1 if r2.first else None),
            "result": 0 if r1.result == XSumoResult.WIN\
                    else "tie" if r1.result == XSumoResult.TIE\
                    else 1 if r2.result == XSumoResult.WIN\
                    else None
        } for r1, r2 in zip(scores[0].score_obj.rounds, scores[1].score_obj.rounds)]

    return ret

@card_renderer.of(XSumoRuleset)
async def render_card(judging):
    return await quart.render_template("judging/event-card-xsumo.html", judging=judging)

@scoring_renderer.of(XSRuleset)
async def render_scoring_xs(judging):
    return await quart.render_template("judging/scoring-xsumo-basic.html",
            judging=judging,
            event_data=get_event_data_xs(judging)
    )

@post_parser.of(XSRuleset)
@autofail_key_error
@check_json
async def parse_post_xs(judging, json):
    try:
        tid1 = int(json["team1"])
        tid2 = int(json["team2"])
    except TypeError as e:
        raise ScoreParserError("Failed to parse team id: %s" % str(e))

    ruleset = get_block(judging.event).ruleset
    s1 = ruleset.create_score()
    s2 = ruleset.create_score()

    for r in json["rounds"]:
        if "first" in r:
            first = r["first"]
            if str(first) not in ("0", "1"):
                raise ScoreParserError("Invalid first value: %s" % first)
            first = int(first)
        else:
            first = None

        if "result" in r:
            res = str(r["result"])

            if res == "tie":
                r1, r2 = "T", "T"
            elif res == "0":
                r1, r2 = "W", "L"
            elif res == "1":
                r1, r2 = "L", "W"
            else:
                raise ScoreParserError("Invalid result: %s" % res)
        else:
            r1, r2 = "L", "L"

        s1.rounds.append(XSRoundScore(first == 0, XSumoResult(r1)))
        s2.rounds.append(XSRoundScore(first == 1, XSumoResult(r2)))

    calc_results(s1, s2)

    return (tid1, s1), (tid2, s2)
