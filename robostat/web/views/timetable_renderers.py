import flask
from robostat.ruleset import Ruleset
from robostat.rulesets.xsumo import XSumoRuleset
from robostat.rulesets.rescue import RescueRuleset
from robostat.rulesets.haastattelu import HaastatteluRuleset
from robostat.web.views.timetable import event_renderer

@event_renderer.of(Ruleset)
def render_default_event(event):
    return flask.render_template("timetable/event.html", event=event)

@event_renderer.of(XSumoRuleset)
def render_xsumo_event(event):
    return flask.render_template("timetable/event-xsumo.html", event=event)

@event_renderer.of(RescueRuleset)
def render_recue_event(event):
    return flask.render_template("timetable/event-rescue.html", event=event)

@event_renderer.of(HaastatteluRuleset)
def render_haastattelu_event(event):
    return flask.render_template("timetable/event-haastattelu.html", event=event)
