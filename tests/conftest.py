import pytest
import robostat
import robostat.db as model
import robostat.web.db
from robostat.web.app import RobostatWeb as _RobostatWeb

class RobostatWeb(_RobostatWeb):
    # Flask tekee tän samalla tavalla omissa testeissään
    # https://github.com/pallets/flask/blob/master/tests/conftest.py
    testing = True
    secret_key = "test key"

@pytest.fixture(scope="session")
def tournament():
    ret = robostat.Tournament()
    with robostat.replace_default_tournament(ret):
        from . import init1
    return ret

@pytest.fixture
def init_app(tournament):
    ret = RobostatWeb("test", tournament=tournament, admin_password="password")
    ret.configure_db("sqlite://")#, engine_args={"echo": "debug"})
    engine = ret.db.get_bind()
    model.Base.metadata.create_all(engine)
    yield ret
    #ret.db.close()

@pytest.fixture
def client(init_app):
    return init_app.test_client()
