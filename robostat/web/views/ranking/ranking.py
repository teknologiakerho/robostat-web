import quart
from sqlalchemy.orm import joinedload, subqueryload
import robostat.db as model
from robostat.web.glob import db, tournament
from robostat.web.util import get_block, field_injector, get_ranking, is_hidden

card_renderer = field_injector("__web_ranking_card_renderer__")
details_renderer = field_injector("__web_ranking_details_renderer__")

# XXX pitäskö field_injectoriin laittaa set_default()?
async def render_default_card(rank, team, score):
    return await quart.render_template("ranking/ranking-card-default.html",
            rank=rank,
            team=team,
            score=score
    )

async def render_default_block(events):
    return await quart.render_template("ranking/block-scores-default.html", events=events)

def source_renderer(renderer=render_default_block):
    def deco(f):
        async def ret(db, **kwargs):
            return await renderer(events=f(db), **kwargs)
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

class RankingView:

    def create_blueprint(self, name="ranking", import_name=__name__, **kwargs):
        b = quart.Blueprint(name, import_name, **kwargs)
        b.add_url_rule("/", "index", self.index)
        b.add_url_rule("/<id>/", "ranking", self.ranking)
        b.add_url_rule("/<id>/details", "details", self.details)
        return b

    async def index(self):
        return await quart.render_template("ranking/list.html",
                rankings=[(id,r) for id,r in tournament.rankings.items() if not is_hidden(r)]
        )

    async def ranking(self, id):
        ranking = get_ranking(id)
        return await quart.render_template("ranking/leaderboard.html",
                name=ranking.name,
                id=ranking.id,
                ranking=ranking(db),
                render_card=card_renderer.get(ranking, default=self.render_rank_card),
                has_details=ranking in details_renderer
        )

    async def details(self, id):
        ranking = get_ranking(id)
        try:
            renderer = details_renderer[ranking]
        except AttributeError:
            quart.abort(404)

        return await renderer(db,
                ranking=ranking,
                name=ranking.name,
                id=ranking.id
        )

    async def render_rank_card(self, rank, team, score):
        renderer = card_renderer.get(score, default=render_default_card)
        return await renderer(rank, team, score)
