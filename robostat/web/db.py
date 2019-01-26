import sqlalchemy as sa
from robostat.db import *
from robostat.util import lazy
from robostat.web.util import decode_score

Team.school = sa.Column(sa.Text, default="", nullable=False)
Team.desc = sa.Column(sa.Text, default="", nullable=False)

Judge.key = sa.Column(sa.Text, unique=True, nullable=False)

Score.score_obj = lazy(decode_score)
