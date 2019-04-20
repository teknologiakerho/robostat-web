import quart
from robostat.rulesets.xsumo import XSumoRuleset
from robostat.rulesets.rescue import RescueRuleset
from robostat.rulesets.tanssi import DanceInterviewRuleset, DancePerformanceRuleset
from robostat.rulesets.haastattelu import HaastatteluRuleset
from robostat.web.views.timetable import event_renderer

@event_renderer.of(XSumoRuleset)
async def render_xsumo_event(event):
    return await quart.render_template("timetable/event-xsumo.html", event=event)

@event_renderer.of(RescueRuleset)
async def render_recue_event(event):
    return await quart.render_template("timetable/event-rescue.html", event=event)

@event_renderer.of(DancePerformanceRuleset)
async def render_dance_event(event):
    return await quart.render_template("timetable/event-dance.html", event=event)

@event_renderer.of(HaastatteluRuleset)
@event_renderer.of(DanceInterviewRuleset)
async def render_haastattelu_event(event):
    return await quart.render_template("timetable/event-haastattelu.html", event=event)
