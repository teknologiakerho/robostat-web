import time
import functools
import logging
import base64
import flask
from sqlalchemy.orm import joinedload, subqueryload
import robostat.db as model
from robostat.ruleset import Ruleset, ValidationError
from robostat.web.glob import db
from robostat.web.util import field_injector, get_block
from robostat.web.login import user, check_login
from robostat.web.logging import request_logger

card_renderer = field_injector("__web_event_card_renderer__")
scoring_renderer = field_injector("__web_scoring_renderer__")
post_parser = field_injector("__web_scoring_post_parser__")

@card_renderer.of(Ruleset)
def render_generic_card(judging):
    return flask.render_template("judging/event-card-generic.html", judging=judging)

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
    def ret(*args, **kwargs):
        json = flask.request.json
        if json is None:
            raise ScoreParserError("Invalid/missing json")
        return f(*args, **kwargs, json=json)
    return ret

class JudgingView(flask.Blueprint):

    def __init__(self, name="judging", import_name=__name__, **kwargs):
        super().__init__(name, import_name, **kwargs)
        self.before_request(check_login)
        self.add_url_rule("/", "index", self.index)
        self.add_url_rule("/list/<what>", "list", self.list)
        self.add_url_rule("/scoring/<int:id>", "scoring", self.scoring, methods=("GET", "POST"))

    def index(self):
        return flask.redirect(flask.url_for(".list", what="future"))

    def list(self, what):
        judgings = self.get_judging_list(user.id, what)
        return self.render_judging_list(judgings)

    def scoring(self, id):
        judging = self.get_judging(user.id, id) or flask.abort(404)

        if flask.request.method == "POST":
            try:
                # TODO flashaa onnistumisen jälkeen että pisteet tallennettiin tjsp
                return self.save_score_post(judging)
            except:
                request_logger.exception("Uncaught exception while saving scores")
                request_logger.log_post_body(logging.ERROR)
                raise

        return self.render_scoring_form(judging)

    def get_judging_list(self, judge_id, what):
        query = db.query(model.EventJudging)\
                .filter_by(judge_id=user.id)\
                .options(
                    joinedload(model.EventJudging.event, innerjoin=True)
                        .subqueryload(model.Event.teams_part)
                        .joinedload(model.EventTeam.team, innerjoin=True)
                )

        if what == "future":
            query = query.filter_by(is_future=True)
        elif what == "past":
            query = query\
                    .filter_by(is_future=False)\
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

    def render_judging_list(self, judgings):
        return flask.render_template("judging/list.html",
                judgings=judgings,
                render_event_card=self.render_event_card
        )

    def render_event_card(self, judging):
        ruleset = get_block(judging.event).ruleset

        try:
            renderer = card_renderer[ruleset]
        except AttributeError:
            return ""

        return renderer(judging)

    def render_scoring_form(self, judging):
        ruleset = get_block(judging.event).ruleset
        return scoring_renderer[ruleset](judging)

    def parse_scoring_post(self, judging):
        ruleset = get_block(judging.event).ruleset
        return post_parser[ruleset](judging)

    def save_score_post(self, judging):
        try:
            scores = self.parse_scoring_post(judging)
        except ScoreParserError as e:
            request_logger.warning("Failed to parse score post: %s" % str(e))
            request_logger.log_post_body(logging.WARNING)
            return str(e), 400

        ruleset = get_block(judging.event).ruleset

        try:
            ruleset.validate(*(s for _,s in scores))
        except ValidationError as e:
            request_logger.warning("Failed to validate scores: %s" % str(e))
            request_logger.log_post_body(logging.WARNING)
            return str(e), 400

        if set(s.team_id for s in judging.scores) != set(s[0] for s in scores):
            request_logger.warning("Received scores for: %s | Expected: %s" % (
                ",".join(str(s[0]) for s in scores),
                ",".join(str(s.team_id) for s in judging.scores)
            ))
            request_logger.log_post_body(logging.WARNING)
            return "Invalid team list", 400

        # Jos tästä tulee joku sqlalchemy virhe vielä nyt vielä validoinnin
        # ja kaiken jälkeen niin se ei oo virhe pyynnössä vaan bugi,
        # joten turha enää tässä try catchata mitään
        self.save_scores(judging, scores)

        request_logger.info("Saved scores [event=%d in block %s]" % (
            judging.event_id,
            judging.event.block_id
        ))

        for team_id, score in scores:
            request_logger.info("Team (id): %d | Score: %s | Base64: %s" % (
                team_id,
                score,
                base64.b64encode(ruleset.encode(score)).decode("utf8")
            ))

        request_logger.log_post_body(logging.DEBUG)

        return "OK: %s" % str(scores)

    def save_scores(self, judging, scores):
        ruleset = get_block(judging.event).ruleset
        team_scores = dict(scores)

        for s in judging.scores:
            s.data = ruleset.encode(team_scores[s.team_id])

        judging.ts = int(time.time())

        db.commit()
