import sys

sys.path.append("/usr/src/app/api")
import falcon
from utils import helpers as hp
from core.settings import config
from services import surveys as sv
from utils import models as md
from third_party.rc_services import RightCareServices

logger = hp.get_logger(config['LOGGER']['SURVEYS_ENDPOINT'], config['LOG_FILES']['SURVEYS_ENDPOINT_LOG'])


class Surveys(object):
    main_endpoint = "survey"

    def __init__(self, rc_service: RightCareServices):
        self.rc_service = rc_service

    def on_get(self, req, resp):
        try:
            logger.info("Customer database informations: %s" % req.context['doc']['database'])
            payload = {
				"status": req.get_param('status'),
				"total": req.get_param('total', default=3000),
				"begin": req.get_param('begin', default=1),
				"search": req.get_param('search'),
				"collection": "surveys",
				"database": req.context['doc']['database']
            }
            result = sv.get_all_surveys(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_post_draft(self, req: falcon.Request, resp: falcon.Response) -> None:
        """
        summary: Save survey as draft in the database
        """
        try:
            current_endpoint = self.main_endpoint + "-" + req.method.lower()
            if not hp.validate_params(current_endpoint, req.context['doc']):
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": config['REQUIRED_FIELDS_MAP'][current_endpoint],
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return

            payload = {
                "collection": "surveys",
                "payload": {
                    "viewid": req.get_param('viewid', None),
                    "name": req.context["doc"].get("name"),
                    "description": req.context["doc"].get("description"),
                    "questions": req.context["doc"].get("questions"),
                    "entrypoint": req.context["doc"].get("entrypoint"),
                    'userId': req.context["doc"].get("userId"),
                    'type': req.context["doc"].get("type"),
                    'settings': req.context["doc"].get("settings"),
                    'subType': req.context["doc"].get("subType", '')
                },
                "database": req.context['doc']['database']
            }
            result = sv.save_survey_as_draft(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_put_publish(self, req, resp, id):
        try:
            payload = {
                "viewid": id,
                "collection": "surveys_publish",
                "database": req.context['doc']['database'],
                "user": req.context['doc']['user'],
                'publickey': req.context['doc'].get('publickey'),
                'apisid': req.context['doc'].get('apisid'),
                'sessionid': req.context['doc'].get('sessionid')
            }
            result = sv.publish_survey(payload, self.rc_service, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_one(self, req, resp, id):
        version_name: str = req.get_param('version_name', None)
        try:
            payload = {
                "viewid": id,
                "version_name": version_name,
                "collection": "surveys",
                "database": req.context['doc']['database']
            }

            result = sv.get_one_survey(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_delete(self, req, resp, id):
        try:
            payload = {
                "viewid": id,
                "collection": "surveys_delete",
                "database": req.context['doc']['database'],
                'publickey': req.context['doc'].get('publickey'),
                'apisid': req.context['doc'].get('apisid'),
                'sessionid': req.context['doc'].get('sessionid')
            }
            logger.info(f'payload = {payload}')
            result = sv.delete_one_survey(payload, self.rc_service, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_put_publish_qrcode(self, req, resp, id, template):
        try:
            payload = {
                "viewid": id,
                "template": template,
                "template_link": req.context["doc"].get("template_link"),
                "collection": "surveys_publish",
                "type": req.context['doc'].get('type', 'single'),
                "names": req.context['doc'].get('names'),
                "database": req.context['doc']['database']
            }
            result = sv.publish_survey_qrcode(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_post_save_publish_template(self, req, resp):
        logger.info(str(req.context['doc']))
        try:
            if not hp.validate_params_by_model(req.context['doc'], md.survey_template):
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": md.survey_template,
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return
            payload = {
                "collection": "surveys_template",
                "payload": {
                    "survey_id": req.context['doc'].get("survey_id"),
                    "image": req.context['doc'].get("image"),
                    "name": req.context['doc'].get("name")
                },
                "database": req.context['doc']['database']
            }
            result = sv.save_publish_survey_template(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_publish_template(self, req, resp, id):
        try:
            payload = {
                "survey_id": id,
                "collection": "surveys_template",
                "database": req.context['doc']['database']
            }
            result = sv.get_publish_survey_template(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_survey_feedback_by_periode(self, req, resp):
        try:
            viewid = req.get_param('viewid', None)
            periode = req.get_param('periode', None)
            channel = req.get_param('channel', None)
            label = req.get_param('label', None)
            version_name = req.get_param('version_name', None)
            if not hp.validate_params_by_model({"viewid": viewid, "periode": periode}, md.survey_periodic_feedback):
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": md.survey_periodic_feedback,
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return
            payload = {
                "collection": "surveys",
                "viewid": viewid,
                "periode": periode,
                "database": req.context['doc']['database'],
                "channel": channel,
                "label": label,
                "version_name": version_name
            }
            if periode == "custom":
                payload["startDate"] = req.get_param('startDate', None)
                payload["endDate"] = req.get_param('endDate', None)

            result = sv.get_survey_feedback_by_periode(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return

        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_survey_list_questions(self, req, resp):
        try:
            viewid = req.get_param('viewid', None)
            version_name = req.get_param('version_name', None)
            if not viewid:
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": "viewid"
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return

            payload = {
                "collection": "surveys",
                "viewid": viewid,
                "version_name": version_name,
                "database": req.context['doc']['database']
            }
            result = sv.get_existing_survey_question_list(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_survey_list_answers(self, req, resp):
        try:
            viewid = req.get_param('viewid', None)
            version_name = req.get_param('version_name', None)
            period, startDate, endDate = req.get_param('period', None), req.get_param('startDate', None), req.get_param(
                'endDate', None)

            if not viewid:
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": "viewid"
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return

            payload = {
                "collection": "surveys",
                "viewid": viewid,
                "version_name": version_name,
                "database": req.context['doc']['database'],
                "period": period,
                "startDate": startDate,
                "endDate": endDate
            }
            result = sv.get_existing_survey_answer_list(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_survey_stats(self, req, resp):
        try:
            viewid = req.get_param('viewid', None)
            questionid = req.get_param('questionid', None)
            channel = req.get_param('channel', None)
            label = req.get_param('label', None)
            version_name = req.get_param('version_name', None)
            period, startDate, endDate = req.get_param('period', None), req.get_param('startDate', None), req.get_param(
                'endDate', None)

            if not viewid and not questionid:
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": ["viewid", "questionid"]
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return

            payload = {
                "collection": "surveys",
                "viewid": viewid,
                "questionid": questionid,
                "database": req.context['doc']['database'],
                "channel": channel,
                "label": label,
                "version_name": version_name,
                "periode": period,
                "startDate": startDate,
                "endDate": endDate
            }

            result = sv.get_stats_by_survey_question(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_survey_reports(self, req, resp):
        try:
            viewid = req.get_param('viewid', None)
            questionid = req.get_param('questionid', None)
            file_type = req.get_param('file_type', None)
            lang = req.get_param('lang', None)
            channel = req.get_param('channel', None)
            label = req.get_param('label', None)
            version_name = req.get_param('version_name', None)
            period = req.get_param('period', None)

            if not viewid or not file_type:
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": ["viewid", "questionid", "file_type"]
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return

            payload = {
                'viewid': viewid,
                'questionid': questionid,
                'collection': 'surveys',
                'file_type': file_type,
                'lang': lang,
                "channel": channel,
                "label": label,
                "version_name": version_name,
                "database": req.context['doc']['database'],
                "user": req.context['doc']['user'],
                "period": period
            }

            if period and period == "custom":
                payload["startDate"] = req.get_param('startDate', None)
                payload["endDate"] = req.get_param('endDate', None)

            result = sv.get_report_by_format(payload, logger)
            logger.info(f"result status : {result[1]}")
            logger.info(f"result filename or error message : {result[0]}")

            if not result[1]:
                resp.status = falcon.HTTP_NOT_FOUND
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"],
                                        {'message': result[0]})
                return

            with open(config['BASE_PATH'] + result[0], 'rb') as f:
                file_data = f.read()
            resp.set_header("Content-Type",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if file_type == 'xlsx' else "application/pdf")
            resp.set_header("Content-Disposition", "attachment; filename=\"%s\"" % result[0])
            resp.data = file_data
            resp.status = falcon.HTTP_OK
            return
        except Exception as e:
            logger.info("This is the error: %s" % e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_put_close_open_survey(self, req, resp):
        try:
            viewid = req.get_param('viewid', None)
            state = req.get_param('state', None)
            if not viewid and not state and state not in ["open", "close"]:
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": {"viewid": {"type": "string"}, "state": {"enum": ["open", "close"]}},
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return

            payload = {
                'viewid': viewid,
                'state': state,
                'collection': 'surveys',
                "database": req.context['doc']['database']
            }
            result = sv.close_or_open_one_survey(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_publish_id(self, req, resp):
        try:
            payload = {
                "viewid": req.get_param('viewid', None),
                "collection": "surveys_publish",
                "database": req.context['doc']['database']
            }
            result = sv.get_publish_survey_id_by_viewid(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_predefined_list(self, req, resp):
        try:
            user_infos = req.context['doc']['user'].get('data')
            # user_language = user_infos['user'].get('language')
            country = user_infos['user'].get('country')
            logger.info("country = %s" % country)
            cities = config['CITIES'][country] if country else config['CITIES']['BJ']
            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], {
                "africa_sub_regions": dict(en=config["SUB_REGIONS_EN"], fr=config["SUB_REGIONS_FR"]),
                "age": dict(en=config["AGE_EN"], fr=config["AGE_FR"]),
                "cities": dict(en=cities, fr=cities),
                "comparison": dict(en=config["COMPARISON_EN"], fr=config["COMPARISON_FR"]),
                "continents": dict(en=config["CONTINENTS_EN"], fr=config["CONTINENTS_FR"]),
                "countries": dict(en=config["COUNTRIES_EN"], fr=config["COUNTRIES_FR"]),
                "days_week": dict(en=config["DAYS_WEEK_EN"], fr=config["DAYS_WEEK_FR"]),
                "employment_type": dict(en=config["EMPLOYMENT_TYPE_EN"], fr=config["EMPLOYMENT_TYPE_FR"]),
                "gender": dict(en=config["GENDER_EN"], fr=config["GENDER_FR"]),
                "how_long": dict(en=config["HOW_LONG_EN"], fr=config["HOW_LONG_FR"]),
                "how_often": dict(en=config["HOW_OFTEN_EN"], fr=config["HOW_OFTEN_FR"]),
                "importance": dict(en=config["IMPORTANCE_EN"], fr=config["IMPORTANCE_FR"]),
                "marital_status": dict(en=config["MARITAL_STATUS_EN"], fr=config["MARITAL_STATUS_FR"]),
                "months_year": dict(en=config["MONTHS_YEAR_EN"], fr=config["MONTHS_YEAR_FR"]),
                "satisfaction": dict(en=config["SATISFACTION_EN"], fr=config["SATISFACTION_FR"]),
                "size": dict(en=config["SIZE_EN"], fr=config["SIZE_FR"]),
                "would_you": dict(en=config["WOULD_YOU_EN"], fr=config["WOULD_YOU_FR"])
            })
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_duplicate_survey(self, req, resp):
        try:
            viewid = req.get_param('viewid', None)
            if not viewid:
                resp.status = falcon.HTTP_BAD_REQUEST
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=dict(code=config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                                                   params=['viewid']))
                return
            payload = {
                "collection": "surveys",
                "viewid": viewid,
                "database": req.context['doc']['database']
            }
            result = sv.duplicate_survey(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_post_export_contacts(self, req, resp):
        try:
            payload = {
                'viewids': req.context["doc"].get("viewids"),
                'type': req.context["doc"].get("type"),
                'survey_id': req.context["doc"].get("survey_id"),
                'collection': 'contacts',
                "database": req.context['doc']['database'],
                "user": req.context['doc']['user']
            }
            result, status = sv.export_contacts(payload, logger)
            if not status:
                if result == 1:
                    resp.status = falcon.HTTP_OK
                    resp.body = hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"])
                    return
                if result == 2:
                    resp.status = falcon.HTTP_OK
                    resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
                    return
            with open(config['BASE_PATH'] + result, 'rb') as f:
                file_data = f.read()
            resp.set_header("Content-Disposition", "attachment; filename=\"%s\"" % result)
            resp.data = file_data
            resp.status = falcon.HTTP_OK
            return
        except Exception as e:
            logger.info("This is the error: %s" % e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_all_contacts(self, req, resp):
        try:
            viewid = req.get_param('viewid', None)
            if not viewid:
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "param": "viewid"
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return
            payload = {
                'collection': 'contacts',
                'viewid': viewid,
                "database": req.context['doc']['database'],
                "user": req.context['doc']['user']
            }
            result = sv.get_all_contacts(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_post_upload_cv_template(self, req, resp):
        try:
            viewid = req.get_param('viewid')
            csvfile = req.get_param('csvfile')
            logger.info(f"Type of viewid: {viewid}")
            logger.info(f"Type of csvfile name : {csvfile.filename}")
            logger.info(f"context attribute named doc : {req.context['doc']}")
            csvfile = csvfile.file.read()

            if not viewid or not csvfile:
                resp.status = falcon.HTTP_BAD_REQUEST
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=dict(code=config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                                                   params=['viewid', 'csvfile']))
                return
            jobpayload = dict(collection="surveys", payload=dict(viewid=viewid, csvfile=csvfile),
                              database=req.context['doc']['database'])
            result = sv.save_template_from_csvfile(jobpayload, logger)
            resp.body = result
            resp.status = falcon.HTTP_OK
            return
        except Exception as e:
            logger.error(f"Failed to upload the csv file: {e}")
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_put_qrcode_download_time(self, req, resp):
        try:
            viewid = req.context["doc"].get('viewid')
            time = req.context["doc"].get('time')
            if not (time and viewid):
                resp.status = falcon.HTTP_BAD_REQUEST
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=dict(code=config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                                                   params=['viewid', 'time']))
                return
            jobpayload: dict = {
                "viewid": viewid,
                "time": time,
                "collection": "surveys",
                "database": req.context['doc']['database']
            }
            result: str = sv.set_download_time_to_survey(jobpayload, logger)
            resp.body = result
            resp.status = falcon.HTTP_OK
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_post_edit_survey(self, req, resp):
        try:
            logger.info(f"Request parameters : {req.context['doc']}")
            if not hp.validate_params_by_model(req.context['doc'], md.edit_survey):
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": md.edit_survey,
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return
            payload = {
                "collection": "surveys",
                "payload": {
                    "name": req.context['doc'].get("name"),
                    "parent": req.context['doc'].get("parent"),
                    "version_name": req.context['doc'].get("version_name"),
                    "description": req.context['doc'].get("description"),
                    "questions": req.context['doc'].get("questions"),
                    "settings": req.context['doc'].get("settings")
                },
                "database": req.context['doc']['database']
            }
            result: str = sv.edit_survey(payload, logger)
            logger.info(f"result : {result}")
            resp.body = result
            resp.status = falcon.HTTP_OK
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_crm_surveys(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            response, status = sv.get_list_for_crm(req.context['doc']['database'], logger)
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

    def on_get_check_deletable(self, req: falcon.Request, resp: falcon.Response) -> None:
        try:
            viewid: str = req.get_param('viewid')
            if not viewid:
                resp.status = falcon.HTTP_BAD_REQUEST
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=dict(code=config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                                                   params=['viewid']))
                return
            payload: dict = {
                'viewid': viewid,
                'publickey': req.context['doc'].get('publickey'),
                'apisid': req.context['doc'].get('apisid'),
                'sessionid': req.context['doc'].get('sessionid'),
                'alias': req.context['doc']['user']["data"]["alias"]
            }
            status, response = sv.check_deleted_survey(payload, self.rc_service, logger)
            if not status:
                resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
                resp.body = response
                return
            resp.status = falcon.HTTP_OK
            resp.body = response
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_get_response_size(self, req, resp) -> None:
        try:
            viewid = req.get_param('viewid', None)
            if not viewid:
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": ["viewid"]
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
                                        error=error)
                return
            size: int = sv.get_total_respondent_for_survey(viewid, req.context['doc']['database'], logger)
            logger.info(f'size : {size}')
            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                                    {'size': size})
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    def on_put_simple_qrcode(self, req, resp) -> None:
        try:
            payload = {
                "viewid": req.get_param('viewid', None),
                "collection": "surveys_publish",
                "database": req.context['doc']['database']
            }
            result = sv.publish_survey_by_simple_qrcode(payload, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception:
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return
