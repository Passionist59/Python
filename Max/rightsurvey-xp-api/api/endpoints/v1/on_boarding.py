import sys

sys.path.append("/usr/src/app/api")
import falcon
from core.settings import config
from logging import Logger
from services.on_boarding import OnBoardingService
from utils import helpers as hp


class OnBoarding(object):

    def __init__(self, service: OnBoardingService, logger: Logger):
        self.service = service
        self.logger = logger

    def on_get_check(self, req, resp):
        try:
            state = self.service.check(req.context['doc'].get('user'), self.logger)
            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config["HTTP_STATUS"]["HTTP_200"], config["ERROR_TITLES"]["HTTP_200"],
                                    data={'state': state})
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config["HTTP_STATUS"]["HTTP_500"], config["ERROR_TITLES"]["HTTP_500"])
            return

    def on_put_update(self, req, resp):
        try:
            self.service.update(req.context['doc'].get('user'), self.logger)
            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config["HTTP_STATUS"]["HTTP_200"], config["ERROR_TITLES"]["HTTP_200"])
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config["HTTP_STATUS"]["HTTP_500"], config["ERROR_TITLES"]["HTTP_500"])
            return
