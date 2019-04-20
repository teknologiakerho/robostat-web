import time
import functools
import logging
import base64
import quart
from sqlalchemy.orm import joinedload, subqueryload, contains_eager
import robostat.db as model
from robostat.ruleset import Ruleset, ValidationError
from robostat.tournament import hide_query_shadows
from robostat.web.glob import db
from robostat.web.util import field_injector, get_block
from robostat.web.login import user, UnauthorizedError
from robostat.web.logging import request_logger

card_renderer = field_injector("__web_event_card_renderer__")
scoring_renderer = field_injector("__web_scoring_renderer__")
post_parser = field_injector("__web_scoring_post_parser__")

@card_renderer.of(Ruleset)
async def render_generic_card(judging):
    return await quart.render_template("judging/event-card-generic.html", judging=judging)

class ScoreParserError(Exception):
    pass

def autofail_key_error(f):
    @functools.wraps(f)
    def ret(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KeyError as e:
            raise ScoreParserError(str(e))
    return ret

def check_json(f):
    @functools.wraps(f)
    async def ret(*args, **kwargs):
        json = await quart.request.json
        if json is None:
            raise ScoreParserError("Invalid/missing json")
        return await f(*args, **kwargs, json=json)
    return ret

class JudgingView:

    hide_shadows = True

    def create_blueprint(self, name="judging", import_name=__name__, **kwargs):
        b = quart.Blueprint(name, import_name, **kwargs)
        b.before_request(self.set_user_id)
        b.context_processor(self.template_context)
        b.add_url_rule("/", "index", self.index)
        b.add_url_rule("/list/<what>", "list", self.list)
        # XXX: Tää viritys siks että javascriptissä saa tehtyä scoring urleja
        b.add_url_rule("/scoring", "scoring_root")
        b.add_url_rule("/scoring/<int:id>", "scoring", self.scoring, methods=("GET", "POST"))
        return b

    async def index(self):
        return quart.redirect(quart.url_for(".list", what="future"))

    async def list(self, what):
        judgings = self.get_judging_list(self.judging_user.id, what)
        return await self.render_judging_list(judgings)

    async def scoring(self, id):
        judging = self.get_judging(self.judging_user.id, id) or quart.abort(404)

        if quart.request.method == "POST":
            try:
                return await self.save_score_post(judging)
            except:
                request_logger.exception("Uncaught exception while saving scores")
                await request_logger.log_post_body(logging.ERROR)
                raise

        return await self.render_scoring_form(judging)

    async def set_user_id(self):
        values = await quart.request.values

        if user.is_admin and "as" in quart.request.values:
            quart.g.judging_user = self.get_faked_user(values.get("as", type=int))\
                    or quart.abort(400)
            quart.g.judging_is_real_user = False
        elif user.logged_in:
            quart.g.judging_user = user
            quart.g.judging_is_real_user = True
        else:
            raise UnauthorizedError()

    @property
    def judging_user(self):
        return quart.g.judging_user

    def template_context(self):
        return {
            "judging_user": self.judging_user,
            "is_real_user": quart.g.judging_is_real_user
        }

    def get_faked_user(self, id):
        return db.query(model.Judge).filter_by(id=id).first()

    def get_judging_list(self, judge_id, what):
        query = db.query(model.EventJudging)\
                .join(model.EventJudging.event)\
                .filter(model.EventJudging.judge_id==judge_id)\
                .options(
                    contains_eager(model.EventJudging.event)
                        .subqueryload(model.Event.teams_part)
                        .joinedload(model.EventTeam.team, innerjoin=True)
                )

        if self.hide_shadows:
            query = hide_query_shadows(query)

        if what == "future":
            query = query.filter(model.EventJudging.is_future)
        elif what == "past":
            query = query\
                    .filter(~model.EventJudging.is_future)\
                    .options(subqueryload(model.EventJudging.scores))

        ret = query.all()
        #print("userid=%d judgings=%s" % (user.id, str(ret)))

        return ret

    def get_judging(self, judge_id, id):
        return db.query(model.EventJudging)\
                .filter_by(judge_id=judge_id, event_id=id)\
                .options(
                    joinedload(model.EventJudging.event, innerjoin=True)
                        .joinedload(model.Event.teams_part, innerjoin=True)
                        .joinedload(model.EventTeam.team, innerjoin=True)
                ).first()

    async def render_judging_list(self, judgings):
        return await quart.render_template("judging/list.html",
                judgings=judgings,
                render_event_card=self.render_event_card
        )

    async def render_event_card(self, judging):
        ruleset = get_block(judging.event).ruleset

        try:
            renderer = card_renderer[ruleset]
        except AttributeError:
            return ""

        return await renderer(judging)

    async def render_scoring_form(self, judging):
        ruleset = get_block(judging.event).ruleset
        return await scoring_renderer[ruleset](judging)

    async def parse_scoring_post(self, judging):
        ruleset = get_block(judging.event).ruleset
        return await post_parser[ruleset](judging)

    async def save_score_post(self, judging):
        try:
            scores = await self.parse_scoring_post(judging)
        except ScoreParserError as e:
            request_logger.warning("Failed to parse score post: %s" % str(e))
            await request_logger.log_post_body(logging.WARNING)
            return str(e), 400

        ruleset = get_block(judging.event).ruleset

        try:
            ruleset.validate(*(s for _,s in scores))
        except ValidationError as e:
            request_logger.warning("Failed to validate scores: %s" % str(e))
            await request_logger.log_post_body(logging.WARNING)
            return str(e), 400

        if set(s.team_id for s in judging.scores) != set(s[0] for s in scores):
            request_logger.warning("Received scores for: %s | Expected: %s" % (
                ",".join(str(s[0]) for s in scores),
                ",".join(str(s.team_id) for s in judging.scores)
            ))
            await request_logger.log_post_body(logging.WARNING)
            return "Invalid team list", 400

        # Jos tästä tulee joku sqlalchemy virhe vielä nyt vielä validoinnin
        # ja kaiken jälkeen niin se ei oo virhe pyynnössä vaan bugi,
        # joten turha enää tässä try catchata mitään
        self.save_scores(judging, scores)

        request_logger.info("Saved scores [event=%d in block %s]" % (
            judging.event_id,
            judging.event.block_id
        ))

        score_info = [(team_id, score, base64.b64encode(ruleset.encode(score)).decode("utf8"))\
                for team_id, score in scores]

        for si in score_info:
            request_logger.info("Team (id): %d | Score: %s | Base64: %s" % si)

        await request_logger.log_post_body(logging.DEBUG)

        saved_mes = await quart.render_template("judging/score-saved-message.html",
                score_info=score_info
        )
        await quart.flash(saved_mes, "success")

        return "OK: %s" % str(score_info)

    def save_scores(self, judging, scores):
        ruleset = get_block(judging.event).ruleset
        team_scores = dict(scores)

        for s in judging.scores:
            s.data = ruleset.encode(team_scores[s.team_id])

        judging.ts = int(time.time())

        db.commit()
