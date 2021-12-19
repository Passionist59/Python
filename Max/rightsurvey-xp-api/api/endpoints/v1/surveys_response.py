import sys

sys.path.append("/usr/src/app/api")
import falcon
from core.settings import config
from utils import models as md
from services import surveys as sv
from logging import Logger
from utils import helpers as hp
import os
from third_party.rp_services import RightPaymentServices


class SurveysResponse(object):
    auth = {
        'auth_disabled': True
    }

    def __init__(self, redis_checker, redis_instance, rp_service: RightPaymentServices, logger: Logger):
        self.redis_checker = redis_checker
        self.redis_instance = redis_instance
        self.rp_service = rp_service
        self.logger = logger

    def on_post_survey_answer(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            if not hp.validate_params_by_model(req.context['doc'], md.survey_answer):
                resp.status = falcon.HTTP_BAD_REQUEST
                error: dict = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": md.survey_answer,
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return
            channel = req.context['doc'].get("channel", {"type": "web", "template": ""})
            self.logger.info(f'channel => {channel}')
            answer = req.context['doc'].get("answer")
            self.logger.info(f'answer => {answer}')
            duration = req.context['doc'].get("duration")
            self.logger.info(f'duration => {duration}')
            respondent = req.context['doc'].get("respondent", "")
            self.logger.info(f'respondent => {respondent}')
            viewid = req.context['doc'].get("viewid")
            self.logger.info(f'viewid => {viewid}')
            version_name = req.context['doc'].get("version_name")
            self.logger.info(f'version_name => {version_name}')

            payload: dict = {
                "collection": "surveys",
                "payload": {
                    "respondent": respondent,
                    "viewid": viewid,
                    "answer": answer,
                    "duration": duration,
                    "channel": channel,
                    "version_name": version_name,
                    "source": req.context['doc'].get("source", "")
                }
            }
            result: str = sv.save_answer_survey(payload, self.redis_checker, self.redis_instance, self.logger, service=None)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_publish(self, req: falcon.Request, resp: falcon.Response, id: str) -> None:
        try:
            self.logger.info(f"Client remote address : {req.remote_addr}")
            payload: dict = {
                "publish_id": id,
                "collection": "surveys_publish"
            }
            result: str = sv.get_one_survey_by_publish_id(payload, self.logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return

        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_post_contact(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            if not hp.validate_params_by_model(req.context['doc'], md.contact):
                resp.status = falcon.HTTP_BAD_REQUEST
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=dict(code=config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                                                   params=md.contact))
                return
            payload: dict = {
                "collection": "contacts",
                "payload": {
                    "viewid": req.context['doc'].get("viewid"),
                    "name": req.context['doc'].get("name"),
                    "phone": req.context['doc'].get("phone")
                }
            }
            result: str = sv.save_contact(payload, self.redis_checker, self.redis_instance, self.logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_daily_report(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            filename: str = req.get_param('filename', None)
            if not filename:
                resp.status = falcon.HTTP_BAD_REQUEST
                error: dict = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": "filename"
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return

            if not os.path.isfile(config["BASE_PATH"] + filename):
                resp.status = falcon.HTTP_OK
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"])
                return

            with open(config["BASE_PATH"] + filename, 'rb') as f:
                file_data: bytes = f.read()
            resp.set_header("Content-Disposition", "attachment; filename=\"%s\"" % filename)
            resp.data = file_data
            resp.status = falcon.HTTP_OK
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_single_qrcode(self, req: falcon.Request, resp: falcon.Response, id: str, template: str) -> None:
        try:
            jobpayload: dict = {
                "publish_id": id,
                "template": template,
                "collection": "surveys_publish"
            }
            result: str = sv.get_one_survey_by_publish_id(jobpayload, self.logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_many_qrcode(self, req: falcon.Request, resp: falcon.Response, id: str, template: str, name: str) -> None:
        try:
            jobpayload: dict = {
                "publish_id": id,
                "template": template,
                "name": name,
                "collection": "surveys_publish"
            }
            result: str = sv.get_one_survey_by_publish_id(jobpayload, self.logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_simple_qrcode(self, req: falcon.Request, resp: falcon.Response, id: str) -> None:
        try:
            jobpayload: dict = {
                "publish_id": id,
                "template": "simple",
                "collection": "surveys_publish"
            }
            result: str = sv.get_one_survey_by_publish_id(jobpayload, self.logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return
