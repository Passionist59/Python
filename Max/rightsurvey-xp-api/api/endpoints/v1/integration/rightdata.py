import sys

sys.path.append("/usr/src/app/api")
import falcon
from utils import helpers as hp
from core.settings import config
from logging import Logger
from redis import StrictRedis
from services.integration import rightdata as rd


class RightData(object):
    auth = {
        'auth_disabled': True
    }

    def __init__(self, logger: Logger, redis_instance: StrictRedis, redis_checker):
        self.logger = logger
        self.redis_instance = redis_instance
        self.redis_checker = redis_checker

    def on_post_link(self, req: falcon.Request, resp: falcon.Response) -> None:
        self.logger.info(f"Request attribute named 'doc' content : {req.context['doc']}")
        try:
            payload: dict = {
                'account': req.context["doc"].get('account'),
                'publickey': req.context["doc"].get('publickey')
            }
            result: bool = rd.link_publickey_to_rightdata_account(payload, self.redis_instance, self.logger)
            payload['state'] = result
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], payload)
            resp.status = falcon.HTTP_OK
            return
        except Exception as e:
            self.logger.info(f"Error occured from rightdata link api : {e}")
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_delete_unlink(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            account: str = req.get_param('account', None)
            self.logger.info(f"account = {account}")
            result = rd.unlink_publickey_to_rightdata_account(account, self.redis_instance, self.logger)
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                                    {'state': result})
            resp.status = falcon.HTTP_OK
            return
        except Exception as e:
            self.logger.info(f"Error occured from rightdata unlink api : {e}")
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_bind_acc_list(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            result: tuple = rd.get_rightdata_account_bind_list(redis_instance=self.redis_instance, logger=self.logger)
            if not result[1]:
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                                        {'message': result[0]})
                resp.status = falcon.HTTP_OK
                return
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], result[0])
            resp.status = falcon.HTTP_OK
            return
        except Exception as e:
            self.logger.info(f"Error occured from rightdata bind account list api : {e}")
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_surveys(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            account: str = req.get_param('account', None)
            payload: dict = {
                'collection': 'surveys',
                'account': account
            }
            result: tuple = rd.get_list_of_surveys(payload, self.redis_instance, self.logger, self.redis_checker)
            if not result[1]:
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                        {'message': result[0]})
                resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
                return
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], result[0])
            resp.status = falcon.HTTP_OK
            return
        except Exception as e:
            self.logger.info(f"Error occured from rightdata ticket list api : {e}")
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_report(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            account: str = req.get_param('account', None)
            viewid: str = req.get_param('viewid', None)
            start_date: str = req.get_param('start_date', None)
            end_date: str = req.get_param('end_date', None)
            filename: str = "rightsurvey.csv"
            payload: dict = {
                'collection': 'surveys',
                'account': account,
                'viewid': viewid,
                'start_date': start_date,
                'end_date' : end_date
            }
            result: tuple = rd.get_csv_report(payload, self.redis_instance, self.logger, self.redis_checker)
            if not result[1]:
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                        {'message': result[0]})
                resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
                return
            resp.set_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            resp.set_header("Content-Disposition", "attachment; filename=\"%s\"" % filename)
            resp.data = result[0]
            resp.status = falcon.HTTP_OK
            return
        except Exception as e:
            self.logger.info(f"Error occured from rightdata report api : {e}")
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return
