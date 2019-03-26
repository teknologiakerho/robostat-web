import collections
import flask
import random # testi
from robostat.util import udict
from robostat.rulesets.xsumo import XSumoRank, XSumoScoreRank, XSumoWinsRank
from robostat.rulesets.rescue import RescueRank, RescueResult
from robostat.web.views.ranking import card_renderer

@card_renderer.of(XSumoRank)
@card_renderer.of(XSumoScoreRank)
def render_xsumo_score_card(rank, team, score):
    return flask.render_template("ranking/ranking-card-xsumo-score.html",
            rank=rank,
            team=team,
            score=score
    )

@card_renderer.of(XSumoWinsRank)
def render_xsumo_wins_card(rank, team, score):
    return flask.render_template("ranking/ranking-card-xsumo-wins.html",
            rank=rank,
            team=team,
            score=score
    )

def render_xsumo_matrix(events, **kwargs):
    d = collections.defaultdict(udict)

    for e in events:
        # xsumo always has 2 scores by 1 judge and either both or none are null
        s1, s2 = e.scores
        if not s1.has_score:
            continue

        sd1 = { "score_value": int(s1.score_obj) }
        sd2 = { "score_value": int(s2.score_obj) }
        ed = {}
        d[s1.team][s2.team] = {"event": ed, "score1": sd1, "score2": sd2}
        d[s2.team][s1.team] = {"event": ed, "score1": sd2, "score2": sd1}

    teams = sorted(d, key=lambda t: t.name)

    if len(events) != len(teams) * (len(teams) - 1) / 2:
        raise ValueError("Invalid number of events, expected %d events for %d teams (got %d)" %(
            len(teams) * (len(teams) - 1) / 2,
            len(teams),
            len(events)
        ))

    team_data = [{"name": t.name} for t in teams]
    event_data = [[d[t1].get(t2) for t2 in teams] for t1 in teams]

    #team_data = [{"name": "Joukkue %d" % i} for i in range(16)]
    #event_data = [[None] * 16 for _ in range(16)]

    #for i in range(16):
    #    for j in range(i+1, 16):
    #        s1 = { "score_value": random.randint(0, 6) }
    #        s2 = { "score_value": random.randint(0, 6) }
    #        event_data[i][j] = { "event": None, "score1": s1, "score2": s2}
    #        event_data[j][i] = { "event": None, "score1": s2, "score2": s1}

    return flask.render_template("ranking/details-xsumo-matrix.html",
            team_data=team_data,
            event_data=event_data,
            **kwargs
    )

def get_rescue_bar(score):
    ret = {
        "F": 0,
        "S": 0,
        "H": 0
    }

    for k,v in score.score_categories:
        val = getattr(score, k)
        if isinstance(val, RescueResult):
            ret[str(val)] += 1
        else:
            ret["F"] += val.fail
            ret["S"] += val.success1
            ret["H"] += val.success2

    return ret

@card_renderer.of(RescueRank)
def render_rescue_card(rank, team, score, max_time=None):
    return flask.render_template("ranking/ranking-card-rescue.html",
            rank=rank,
            team=team,
            score=score,
            max_time=max_time,
            bar_data=get_rescue_bar(score.best)
    )

def rescue_card_renderer(ruleset):
    return lambda rank, team, score: render_rescue_card(rank, team, score, ruleset.max_time)
