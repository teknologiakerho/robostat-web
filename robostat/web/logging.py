import logging
import quart
from robostat.web.login import user

logger = logging.getLogger("robostat.web")

class RequestLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        ret = "[%s %s %s] %s" % (
            quart.request.remote_addr,
            quart.request.method,
            quart.request.full_path,
            msg
        )

        if user.logged_in:
            ret = "[%s:%d] %s" % (
                user.name,
                user.id,
                ret
            )

        return ret, kwargs

    async def log_post_body(self, level=logging.INFO):
        data = await quart.request.get_data()
        return self.log(level, data.decode("utf8"))

request_logger = RequestLoggerAdapter(logger, None)
