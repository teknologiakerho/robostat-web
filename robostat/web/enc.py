from robostat.ruleset import Ruleset
from robostat.web.util import field_injector

json_encoder = field_injector("__web_json_enc__")

@json_encoder(Ruleset)
def generic_encode_score(score):
    return {"score_value": int(score)}
