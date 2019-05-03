import robostat.db as model
from robostat.tournament import RankProxy
from robostat.rulesets.xsumo import XSumoRank
from robostat.rulesets.rescue import RescueRank, RescueScore
from robostat.web.views.api import jsonifier

@jsonifier.of(RankProxy)
def jsonify_rank_proxy(proxy):
    # TODO: tässä vois palauttaa tietoa myös mitä muuta tuossa proxyssä on?
    return jsonifier[proxy.rank](proxy.rank)

@jsonifier.of(XSumoRank)
def jsonify_xsumo_rank(rank):
    return {
        "score": rank.score,
        "wins": rank.wins,
        "ties": rank.ties,
        "losses": rank.losses,
        "unplayed": rank.unplayed
    }

@jsonifier.of(RescueRank)
def jsonify_rescue_rank(rank):
    return {
        "best": jsonifier[rank.best](rank.best),
        "others": [(jsonifier[s](s) if s is not None else None) for s in rank.other_scores]
    }

@jsonifier.of(RescueScore)
def jsonify_rescue_score(score):
    return {
        "score": int(score),
        "time": score.time
    }

@jsonifier.of(model.Team)
def jsonify_team(team):
    return {
        "id": team.id,
        "name": team.name,
        "school": team.school
    }

@jsonifier.of(model.Judge)
def jsonify_judge(judge):
    return {
        "id": judge.id,
        "name": judge.name
    }
