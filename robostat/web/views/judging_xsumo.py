import flask
from robostat.rulesets.xsumo import XSumoRuleset, XSRuleset, XSRoundScore, XIRuleset,\
        XIRoundScore, XMRuleset, XMRoundScore, WIN, LOSE, TIE, calc_results
from robostat.web.util import get_block
from robostat.web.views.judging import card_renderer, scoring_renderer, post_parser

def get_basic_event_data(judging):
    ret = {}

    ret["teams"] = [{
        "id": s.team.id,
        "name": s.team.name
        } for s in sorted(judging.scores, key=lambda x: x.team.name)]

    if not judging.is_future:
        ret["rounds"] = [{
            "first": 0 if r1.first else (1 if r2.first else None),
            "result": 0 if r1.result == WIN\
                    else "tie" if r1.result == TIE\
                    else 1 if r2.result == WIN\
                    else None
        } for r1, r2 in zip(judging.scores[0].score_obj.rounds,judging.scores[1].score_obj.rounds)]

    return ret

def iter_post_key(key):
    i = 0
    while True:
        try:
            yield i, flask.request.form[key % i]
        except KeyError:
            return
        i += 1

@card_renderer.of(XSumoRuleset)
def render_card(judging):
    return flask.render_template("judging/event-card-xsumo.html", judging=judging)

@scoring_renderer.of(XSRuleset)
def render_basic_scoring(judging):
    return flask.render_template("judging/scoring-xsumo-basic.html",
            judging=judging,
            event_data=get_basic_event_data(judging)
    )

@post_parser.of(XSRuleset)
def parse_basic_post(judging):
    json = flask.request.json

    tid0 = int(json["team1"])
    tid1 = int(json["team2"])

    ruleset = get_block(judging.event).ruleset
    s0 = ruleset.create_score()
    s1 = ruleset.create_score()

    for r in json["rounds"]:
        first = "first" in r and int(r["first"])

        if "result" in r:
            res = r["result"]
            if res == "tie":
                r0, r1 = TIE, TIE
            elif res == "0":
                r0, r1 = WIN, LOSE
            else:
                r0, r1 = LOSE, WIN
        else:
            r0, r1 = LOSE, LOSE

        s0.rounds.append(XSRoundScore(first == 0, r0))
        s1.rounds.append(XSRoundScore(first == 1, r1))

    calc_results(s0, s1)

    return (tid0, s0), (tid1, s1)

def get_innokas_event_data(judging):
    ret = {}
    ret["teams"] = [t.name for t in judging.event.teams]
    if not judging.is_future:
        ret["rounds"] = [{
            "first": 0 if r1.first else (1 if r2.first else None),
            "pseudorounds": [p1 if p1 > 0 else -p2 for p1,p2 in zip(r1.pseudorounds,
                r2.pseudorounds)]
        } for r1, r2 in zip(judging.scores[0].score_obj.rounds,judging.scores[1].score_obj.rounds)]

    return ret

@scoring_renderer.of(XIRuleset)
def render_innokas_scoring(judging):
    return flask.render_template("judging/scoring-xsumo-innokas.html",
            judging=judging,
            event_data=get_innokas_event_data(judging)
    )

@post_parser.of(XIRuleset)
def parse_innokas_post(judging):
    # TODO check for problems (missing keys etc) and warn

    tid0 = int(flask.request.form["team0"])
    tid1 = int(flask.request.form["team1"])
    ruleset = get_block(judging.event).ruleset
    s0 = ruleset.create_score()
    s1 = ruleset.create_score()

    for rnum, first in iter_post_key("first.%d"):
        results = [int(res) for _, res in iter_post_key("result.%d.%%d" % rnum)]
        s0.rounds.append(XIRoundScore(int(first) == 0, [max(r, 0) for r in results]))
        s1.rounds.append(XIRoundScore(int(first) == 1, [max(-r, 0) for r in results]))

    calc_results(s0, s1)

    return (tid0, s0), (tid1, s1)
