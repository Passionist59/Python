import sys

sys.path.append("/usr/src/app/api")
import falcon
from utils import helpers as hp
from core.settings import config
from logging import Logger
from services.integration import rightcare as rc
from third_party.xp_services import AccountCustomerService
from third_party.rc_services import RightCareServices

logger: Logger = hp.get_logger(config['LOGGER']['RIGHTCARE_INTEGRATION_LOGGER'],
                               config['LOG_FILES']['RIGHTCARE_INTEGRATION_LOG'])


class RightCare(object):

    def __init__(self, xp_account: AccountCustomerService, rc_service: RightCareServices):
        self.xp_account = xp_account
        self.rc_service = rc_service

    def on_get_survey_list(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            payload: dict = {
                "collection": "surveys",
                "database": req.context['doc']['database']
            }
            result: tuple = rc.get_list_of_template_surveys(payload, logger)
            resp.status = falcon.HTTP_OK
            if not result[1]:
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"],
                                        {'message': result[0]})
                return
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], result[0])
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_rightcare_agents(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            payload: dict = {
                'publickey': req.context['doc'].get('publickey'),
                'apisid': req.context['doc'].get('apisid'),
                'sessionid': req.context['doc'].get('sessionid')
            }
            status, response = rc.get_plateform_agents(payload, self.rc_service, logger)
            logger.info(f'status : {status} | response : {response}')
            resp.status = falcon.HTTP_OK
            if not status:
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], {},
                                        {'message': response})
                return
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], response)
            return

        except Exception as e:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], {},
                                    {'message': f'{e}'})
            return

    def on_get_apps_purchased(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:

            publickey: str = req.context['doc']['publickey']
            apisid: str = req.context['doc']['apisid']
            sessionid: str = req.context['doc']['sessionid']

            status, resp_data = self.xp_account.get_client_app(publickey, apisid, sessionid)
            logger.info(f'status : {status}')
            logger.info(f'data : {resp_data}')

            if not status:
                resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                        {'message': resp_data['message']})
                return

            apps: list = resp_data['apps']
            logger.info(f'apps : {apps}')
            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                                    list(map(lambda x: x['app_code'], apps)))
            return

        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_priorities(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            lang = req.get_param('lang', 'en')
            lang = lang.upper()
            logger.info(f'lang = {lang}')
            response = config[f'PRIORITY_{lang}']
            logger.info(f'response = {response}')
            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                                    config[f'PRIORITY_{lang.upper()}'])
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_post_save_config(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            viewids: list = req.context['doc'].get('viewids')
            priority: int = req.context['doc'].get('priority')
            agent: str = req.context['doc'].get('agent')
            if not (viewids and priority and agent):
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": ['viewids', 'priority', 'agent'],
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return
            logger.info('*******************************')
            logger.info(req.context['doc'])
            logger.info('*******************************')
            payload: dict = {
                'viewids': viewids,
                'priority': priority,
                'agent': agent,
                'publickey': req.context['doc'].get('publickey'),
                'apisid': req.context['doc'].get('apisid'),
                'sessionid': req.context['doc'].get('sessionid'),
                "database": req.context['doc']['database']
            }
            logger.info(f'Payload = {payload}')
            result: tuple = rc.save_configuration(payload, self.rc_service, logger)
            if not result[1]:
                resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                        {'message': result[0]})
                return
            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"])
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_put_update_config(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            viewid: str = req.context['doc'].get('viewid')
            priority: int = req.context['doc'].get('priority')
            agent: str = req.context['doc'].get('agent')
            if not (viewid and priority and agent):
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": ['viewid', 'priority', 'agent'],
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return

            payload: dict = {
                'viewid': viewid,
                'priority': priority,
                'agent': agent,
                'publickey': req.context['doc'].get('publickey'),
                'apisid': req.context['doc'].get('apisid'),
                'sessionid': req.context['doc'].get('sessionid'),
                "database": req.context['doc']['database']
            }

            result: tuple = rc.update_configuration(payload, self.rc_service, logger)
            if not result[1]:
                resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                        {'message': result[0]})
                return
            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"])
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_delete_remove_config(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            viewid: str = req.get_param('viewid')
            if not viewid:
                resp.status = falcon.HTTP_BAD_REQUEST
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"], error={})
                return
            payload: dict = {
                'viewid': viewid,
                'publickey': req.context['doc'].get('publickey'),
                'apisid': req.context['doc'].get('apisid'),
                'sessionid': req.context['doc'].get('sessionid'),
                "database": req.context['doc']['database']
            }
            response, status = rc.delete_configuration(payload, self.rc_service, logger)
            if not status:
                resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                        {'message': response})
            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"])
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_connect_status(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            response, status = rc.check_connection_to_rightcare(req.context['doc']['database'], logger)
            if not status:
                resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                        {'message': response})
            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], response)
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_connected_surveys(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            payload: dict = {
                'publickey': req.context['doc'].get('publickey'),
                'apisid': req.context['doc'].get('apisid'),
                'sessionid': req.context['doc'].get('sessionid'),
                "database": req.context['doc']['database']
            }
            response, status = rc.get_list_surveys_connect_to_rightcare(payload, self.rc_service, logger)
            if not status:
                resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                        {'message': response})
            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], response)
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_put_disconnect(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            viewid: str = req.get_param('viewid')
            payload: dict = {
                'viewid': viewid,
                'publickey': req.context['doc'].get('publickey'),
                'apisid': req.context['doc'].get('apisid'),
                'sessionid': req.context['doc'].get('sessionid'),
                "database": req.context['doc']['database']
            }
            response, status = rc.disconnect_specific_survey(payload, self.rc_service, logger)
            if not status:
                resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], response)
            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], response)
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_put_disconnect_all(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            payload: dict = {
                'publickey': req.context['doc'].get('publickey'),
                'apisid': req.context['doc'].get('apisid'),
                'sessionid': req.context['doc'].get('sessionid'),
                "database": req.context['doc']['database']
            }
            response, status = rc.disconnect_all_surveys(payload, self.rc_service, logger)
            if not status:
                resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], response)
            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], response)
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_post_create_ticket(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            logger.info(req.context['doc'])
            payload: dict = {
                "viewid": req.context['doc'].get('viewid'),
                "firstname": req.context['doc'].get('firstname', ''),
                "email": req.context['doc'].get('email', ''),
                "phone": req.context['doc'].get('phone', ''),
                "message": req.context['doc'].get('message', ''),
                "collection": "surveys_publish"
            }
            logger.info(f'Payload = {payload}')
            result: tuple = rc.create_ticket_for_selected_survey(payload, self.rc_service, logger)

            if not result[1]:
                resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                        {'message': result[0]})
                return

            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"])
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return
