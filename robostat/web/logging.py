import logging
import flask
from robostat.web.login import user

logger = logging.getLogger("robostat.web")

class RequestLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        ret = "[%s %s %s] %s" % (
            flask.request.remote_addr,
            flask.request.method,
            flask.request.full_path,
            msg
        )

        if user.logged_in:
            ret = "[%s:%d] %s" % (
                user.name,
                user.id,
                ret
            )

        return ret, kwargs

    def log_post_body(self, level=logging.INFO):
        return self.log(level, str(flask.request.form))

request_logger = RequestLoggerAdapter(logger, None)
