import sys

sys.path.append("/usr/src/app/api")
import falcon
from utils import helpers as hp
from core.settings import config
from third_party.xp_services import AccountCustomerService

logger = hp.get_logger(config["LOGGER"]['SESSION_ENDPOINT'], config["LOG_FILES"]['SESSION_ENDPOINT_LOG'])


class Sessions(object):
    auth = {
        'auth_disabled': True
    }

    def __init__(self, xp_account: AccountCustomerService):
        self.xp_account = xp_account

    def on_get(self, req, resp):
        try:
            alias = req.get_param('alias', None)
            sid = req.get_param('sid', None)
            app_id = req.get_param('app_id', None)
            logger.info(
                "Get session informations -> " + alias + " with app -> " + app_id + ", sid -> " + sid)

            if not alias or not app_id or not alias or not sid:
                resp.status = falcon.HTTP_BAD_REQUEST
                resp.body = hp.response(config["HTTP_STATUS"]["HTTP_400"], config["ERROR_TITLES"]["HTTP_400"],
                                        error={"code": config["ERROR_CODE"]["MISSING_DATABASE_PARAMETERS"],
                                               "params": ["sid", "app_id", "alias"]})
                return

            response = self.xp_account.session_decoder(alias, app_id, sid)

            logger.info('Session data status => %s' % response[0])

            logger.info('Session data receive => %s' % response[1])

            if response[0]:
                logger.info('Session data receive => %s' % response[1])
                resp.status = falcon.HTTP_OK
                resp.body = hp.response(config["HTTP_STATUS"]["HTTP_200"], config["ERROR_TITLES"]["HTTP_200"],
                                        data=response[1])
                return

            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config["HTTP_STATUS"]["HTTP_404"], config["ERROR_TITLES"]["HTTP_404"])
            return
        except Exception as e:
            logger.info("There is an error on get user session: %s" % e)
            resp.status = falcon.HTTP_200
            resp.body = hp.response(config["HTTP_STATUS"]["HTTP_500"], config["ERROR_TITLES"]["HTTP_500"])
            return
