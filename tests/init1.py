import robostat
from robostat.tournament import aggregate_scores, sort_ranking, decode_block_scores
from robostat.rulesets.xsumo import XSRuleset, XSumoScoreRank
from robostat.rulesets.rescue import RescueRuleset, RescueMaxRank
from robostat.web.views.ranking import card_renderer, details_renderer, make_block_renderer
from robostat.web.views.ranking.renderers import render_xsumo_matrix, rescue_card_renderer

xsumo_ruleset = XSRuleset()
rescue1_ruleset = RescueRuleset.by_difficulty(1, max_time=600)

xsumo_alkusarja = robostat.block(
        id="xsumo.as",
        ruleset=xsumo_ruleset,
        name="XSumo alkusarja"
)

rescue1_a = robostat.block(
        id="rescue1.a",
        ruleset=rescue1_ruleset,
        name="Rescue 1 (A)"
)

rescue1_b = robostat.block(
        id="rescue1.b",
        ruleset=rescue1_ruleset,
        name="Rescue 1 (B)"
)

@robostat.ranking("xsumo.as", name="XSumo alkusarja")
@details_renderer(make_block_renderer(xsumo_alkusarja, render_xsumo_matrix))
def rank_xsumo_as(db):
    scores = xsumo_alkusarja.decode_scores(db)
    ranks = aggregate_scores(scores, XSumoScoreRank.from_scores)
    return sort_ranking(ranks.items())

@robostat.ranking("rescue1", name="Rescue 1")
@card_renderer(rescue_card_renderer(rescue1_ruleset))
def rank_rescue1(db):
    scores = decode_block_scores(db, rescue1_a, rescue1_b)
    ranks = aggregate_scores(scores, RescueMaxRank.from_scores)
    return sort_ranking(ranks.items())
