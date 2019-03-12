import flask
from sqlalchemy.orm import joinedload, subqueryload
import robostat.db as model
from robostat.web.glob import db
from robostat.web.util import get_block, field_injector, get_ranking

card_renderer = field_injector("__web_ranking_card_renderer__")
details_renderer = field_injector("__web_ranking_details_renderer__")

from robostat.web.views.ranking_renderers import render_default_block, render_default_card

def source_renderer(renderer=render_default_block):
    def deco(f):
        def ret(db, **kwargs):
            return renderer(events=f(db), **kwargs)
        return ret
    return deco

def make_block_renderer(block, renderer=render_default_block):
    def ret(db, **kwargs):
        events = block.events_query(db)\
            .options(
                joinedload(model.Event.scores, innerjoin=True),
                joinedload(model.Event.teams_part, innerjoin=True)
                .joinedload(model.EventTeam.team, innerjoin=True)
            )\
            .all()
        return renderer(events=events, **kwargs)
    return ret

class RankingView(flask.Blueprint):

    def __init__(self, name="ranking", import_name=__name__, **kwargs):
        super().__init__(name, import_name, **kwargs)
        self.add_url_rule("/", "index", self.index)
        self.add_url_rule("/<id>/", "ranking", self.ranking)
        self.add_url_rule("/<id>/details", "details", self.details)

    def index(self):
        return ""

    def ranking(self, id):
        ranking = get_ranking(id)
        return flask.render_template("ranking/leaderboard.html",
                name=ranking.name,
                id=ranking.id,
                ranking=ranking(db),
                render_card=card_renderer.get(ranking, default=self.render_rank_card),
                has_details=ranking in details_renderer
        )

    def details(self, id):
        ranking = get_ranking(id)
        try:
            renderer = details_renderer[ranking]
        except AttributeError:
            flask.abort(404)

        return renderer(db,
                ranking=ranking,
                name=ranking.name,
                id=ranking.id
        )

    def render_rank_card(self, rank, team, score):
        renderer = card_renderer.get(score, default=render_default_card)
        return renderer(rank, team, score)
