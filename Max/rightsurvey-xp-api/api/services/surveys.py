# -*- coding: utf-8 -*-
import sys

sys.path.append("/usr/src/app/api")
from core.settings import config
from utils import helpers as hp
from core.dbutils import get_list, add, edit_one, get_one, delete, execute_aggregation, add_to_public, \
    check_collection_exists, add_collection, edit_many
from core.data_to_pdf_v2 import DataToPdf
from reportlab.platypus import Paragraph as P
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from core.data_to_excel import DataToExcel

from logging import Logger
import csv
import codecs, io
from third_party.rc_services import RightCareServices
from third_party.rp_services import RightPaymentServices
from services.integrations import check_survey_assigned
from datetime import datetime as dt
from urllib.parse import quote
import json
from utils.periode_converter import PeriodeConverter
from utils.query_builder import QueryBuilder
from utils.datetime_converter import DatetimeConverter

styles = getSampleStyleSheet()
styleN = styles["BodyText"]
styleBH = styles["Normal"]
styleBH.alignment = TA_CENTER


# Service which return a list of survey
def get_all_surveys(jobpayload, logger):
    try:
        collection, database = jobpayload['collection'], jobpayload['database']
        total, begin = int(jobpayload['total']), int(jobpayload['begin'])
        status, search = jobpayload['status'], jobpayload['search']
        match = {"$match": {"parent": {"$exists": False}}}
        total_respondent_cond = {"if": {"$isArray": "$answers"}, "then": {"$size": "$answers"}, "else": 0}
        project_fields = {"_id": 0, "viewid": 1, "name": 1, "status": 1, "type": 1, "subType": 1,
						  "created_at": 1, "updated_at": 1, "total_respondent": {"$cond": total_respondent_cond}}
        project = {"$project": project_fields}
        if status: match["$match"]["status"] = int(status)
        skip: int = total * (begin - 1)
        pipeline = [match, {'$sort': {'created_at': -1}}, {'$skip': skip}, {'$limit': total}, project]
        result, _ = execute_aggregation(database["dbname"], database["dbuser"], database["dbpassword"], collection,
										pipeline)
        logger.info(f"result : {result}")
        if not result:
            return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], [])

        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], result)

    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_all_surveys", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
    
#    try:
#        projection: dict = {'_id': False, 'id': False, 'created_at': False, "answers": False}
#
#        criteria = {"parent": {"$exists": False}}
#        paginator = None
#        limit = 0
#        if jobpayload["search"]:
#            criteria["$text"] = {"$search": jobpayload["search"]}
#        if jobpayload["total"] and jobpayload["begin"]:
#            paginator['skip'] = jobpayload["begin"]
#            paginator['limit'] = jobpayload["total"]
#        elif jobpayload["total"] and not jobpayload["begin"]:
#            limit = int(jobpayload["total"])
#
#        collection = jobpayload['collection']
#        logger.info(f'collection : {collection}')
#        database = jobpayload['database']
#        logger.info(f'database : {database}')
#        query_data: dict = {
#            'database': database["dbname"],
#            'username': database["dbuser"],
#            'pwd': database["dbpassword"],
#            'collection': collection,
#            'criteria': criteria,
#            'sort': [('created_date', -1)],
#            'limit': limit,
#            'paginator': paginator,
#            'projection': projection
#        }
#        result = get_list(**query_data)
#        logger.info(f"result : {result}")
#        surveys = []
#        if result[1] and result[0]:
#            for survey in result[0]:
#                survey["total_respondent"] = len(survey["answers"]) if "answers" in survey else 0
#                if survey["status"] == 2 and "questions" in survey:
#                    del survey["questions"]
#                if survey["status"] == 2 and "answers" in survey:
#                    del survey["answers"]
#                if survey.get("versions"):
#                    survey_versions = survey.get("versions")
#                    version_size = len(survey_versions)
#                    last_version = survey_versions[version_size - 1]
#                    logger.info(f"last version name : {last_version}")
#                    last_version_survey, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'],
#                                                     collection,
#                                                     {'parent': survey['viewid'], 'version_name': last_version})
#                    if last_version_survey:
#                        survey['settings'] = last_version_survey.get('settings')
#                        if survey.get('questions'):
#                            survey['questions'] = last_version_survey.get('questions')
#                surveys.append(survey)
#        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], surveys)
#    except Exception as e:
#        logger.info(config["METHOD_ERROR_MSG"].format("get_all_surveys", e))
#        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


# Service which allow to save as draft
def save_survey_as_draft(jobpayload, logger):
    try:
        payload = jobpayload['payload']
        collection = jobpayload['collection']
        database = jobpayload['database']
        settings = payload['settings']
        survey = {"name": payload["name"], "description": payload["description"], "questions": payload["questions"],
                  "status": 0, "entrypoint": payload['entrypoint'], "userId": payload['userId'],
                  "type": payload['type'], "subType": payload["subType"], "settings": settings}
        response = {"viewid": None}
        if not payload['viewid']:
            result = add(database["dbname"], database["dbuser"], database["dbpassword"], collection, survey,
                         listback=False)
            logger.info(f'result: {result[0]}')
            response['viewid'] = result[0]
        else:
            edit_one(database=database["dbname"], username=database["dbuser"], pwd=database["dbpassword"],
                     collection=collection, criteria={'viewid': payload['viewid']}, param=survey, type='$set',
                     listback=False)
            response['viewid'] = payload['viewid']
        logger.info(f'payload => {payload}')
        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], response)
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("save_survey_as_draft", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


# Service which get an survey by viewid
def get_one_survey(jobpayload, logger):
    try:
        projection: dict = {'_id': False, 'id': False, 'created_at': False}
        collection = jobpayload['collection']
        database = jobpayload['database']
        version_name = jobpayload['version_name']
        survey, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                 {'viewid': jobpayload['viewid']}, projection)
        if status and survey:
            total_response: int = get_total_respondent_for_survey(jobpayload['viewid'], database, logger)
            logger.info(f'total_response = {total_response}')
            if survey['status'] == 2:
                hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                            data={"message": "Sorry this survey is closed actually",
                                  "settings": survey["settings"] if survey["settings"] else {}})
            if 'versions' in survey:
                last_version = survey['versions'][-1]
                survey_version, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                            {'parent': jobpayload['viewid'], 'version_name': last_version})
                survey['questions'] = survey_version['questions']
                survey['settings'] = survey_version['settings']

            if version_name:
                survey_version, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                            {'parent': jobpayload['viewid'], 'version_name': version_name})
                if not survey_version:
                    return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"],
                                       {'message': f'The version : {version_name} of survey is not found'})
                survey['questions'] = survey_version['questions']
                survey['settings'] = survey_version['settings']
            survey['total_respondent'] = total_response
            return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], survey)
        return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"])
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_one_survey", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


# Service which publish an survey and return a fill url generated
def publish_survey(jobpayload, service: RightCareServices, logger):
    try:
        collection = jobpayload['collection']
        database = jobpayload['database']
        user = jobpayload['user']
        viewid = jobpayload['viewid']
        surveys_collection = "surveys"
        result = get_one(database['dbname'], database['dbuser'], database['dbpassword'], surveys_collection,
                         {'viewid': viewid})
        if result[1] and result[0]:
            survey = result[0]
            publish_id = hp.generate_sharable_id(length=20)
            survey['status'] = 1
            survey['publish_id'] = publish_id
            survey['publickey'] = user['data']['alias']
            result = add_to_public(config["PUBLIC_DB_NAME"], config["PUBLIC_DB_USER"], config["PUBLIC_DB_PWD"],
                                   collection, survey, False)
            if result[1] and result[0]:
                edit_one(database=database['dbname'], username=database['dbuser'], pwd=database['dbpassword'],
                         collection=surveys_collection,
                         criteria={'viewid': viewid}, param={"status": 1}, type='$set', listback=False)
                settings = survey['settings']
                if settings.get("connectRightcare") == True:
                    priority = settings["rightcareData"]["priority"]
                    agent = settings["rightcareData"]["agent"]
                    header: dict = {'publickey': jobpayload.get('publickey'), 'apisid': jobpayload.get('apisid'),
                                    'sessionid': jobpayload.get('sessionid')}
                    status, resp_data = service.create_configuration(
                        {'survey_id': viewid, 'title': survey['name'], 'priority_id': priority,
                         'assigned_agent_id': agent}, header)
                    logger.info(f'RightCare config saver status : {status} and response : {resp_data}')
                return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                                   {'publish_id': publish_id})
            return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                               {'message': 'Something was wrong in publish survey processing'})

        return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"])
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("publish_survey", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


# Service which get published survey by publish id
def get_one_survey_by_publish_id(jobpayload, logger):
    try:
        collection = jobpayload['collection']
        publish_id = jobpayload["publish_id"]
        logger.info(f"publish_id => {publish_id}")
        template = jobpayload.get("template", None)

        name = jobpayload.get("name", None)
        survey, status = get_one(config["PUBLIC_DB_NAME"], config["PUBLIC_DB_USER"], config["PUBLIC_DB_PWD"],
								 collection, {"publish_id": publish_id})
        if status and survey:

            qrcode_setting = survey.get("qrcode_settings")
            if qrcode_setting and template and qrcode_setting["template"]["name"] != template:
                return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"])
            if qrcode_setting and name and name not in qrcode_setting["template"]["names"]:
                return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"])
            if survey["status"] == 1:
                # status, result = service.get_account_status(survey["publickey"])
                # logger.info(f'status = {status}, result = {result}')
                # if not status:
                # 	raise Exception("Oups we are not able to retrieve account status")
                # number_responses, used_responses = result['number_responses'], result['used_responses']
                # limit_exceed = number_responses > 0 and number_responses >= used_responses
                # survey['limit_exceed'] = (not limit_exceed)
                survey['limit_exceed'] = False
                survey.pop("publickey")
                return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                                   data=survey)
            if survey["status"] == 2:
                return hp.response(config['HTTP_STATUS']["HTTP_406"], config['ERROR_TITLES']["HTTP_406"],
                                   data={"settings": survey["settings"] if survey["settings"] else {}})
        return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"])
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_one_survey_by_publish_id", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def publish_survey_by_simple_qrcode(jobpayload: dict, logger: Logger) -> str:
    try:
        viewid = jobpayload['viewid']
        database = jobpayload['database']
        result: str = get_publish_survey_id_by_viewid(jobpayload, logger)
        dict_result: dict = json.loads(result)
        if dict_result.get("status") == config['HTTP_STATUS']["HTTP_200"]:
            edit_one(database=database['dbname'], username=database['dbuser'], pwd=database['dbpassword'],
                     collection='surveys', criteria={'viewid': viewid}, param={"simple_qrcode": True}, type='$set',
                     listback=False)
        return result
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("publish_survey_by_simple_qrcode", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def get_publish_survey_id_by_viewid(jobpayload, logger):
    try:
        collection = jobpayload['collection']
        viewid = jobpayload['viewid']
        database = jobpayload['database']
        query = {"viewid": viewid}
        survey, status = get_one(config["PUBLIC_DB_NAME"], config["PUBLIC_DB_USER"], config["PUBLIC_DB_PWD"],
                                 collection, query)
        if not (status and survey):
            return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"])
        if survey.get("status") == 2:
            result = close_or_open_one_survey(
                {"collection": "surveys", "database": database, "state": "open", "viewid": viewid}, logger)
            logger.info(f"response after edit survey status : {result}")
        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                           data=survey["publish_id"])
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_publish_survey_id_by_viewid", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def delete_one_survey(jobpayload: dict, service: RightCareServices, logger: Logger):
    try:
        collection, database  = jobpayload['collection'], jobpayload['database']
        viewid, publickey = jobpayload['viewid'], jobpayload['publickey']
        apisid, sessionid = jobpayload['apisid'], jobpayload['sessionid']
        survey, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'], 'surveys',
                            {"viewid": viewid})
        logger.info(f'survey with viewid : {viewid} details : {survey}')
        if not survey:
            return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"])
        settings: dict = survey["settings"]
        logger.info(f'settings : {settings}')
        connect_to_rightcare: bool = settings.get('connectRightcare', False)
        logger.info(f'connectRightcare : {connect_to_rightcare}')

        if connect_to_rightcare: service.delete_configuration(viewid, {'publickey': publickey, 'apisid': apisid,
                                                                       'sessionid': sessionid})

        if survey['status'] == 1:
            edit_one(database=config["PUBLIC_DB_NAME"], username=config["PUBLIC_DB_USER"], pwd=config["PUBLIC_DB_PWD"],
                     collection="surveys_publish", criteria={'viewid': viewid}, param={"status": 2}, type='$set',
                     listback=False)

        add(database['dbname'], database['dbuser'], database['dbpassword'], collection, survey, listback=False)

        edit_one(database=config["PUBLIC_DB_NAME"], username=config["PUBLIC_DB_USER"], pwd=config["PUBLIC_DB_PWD"],
                 collection="surveys_publish", criteria={'viewid': viewid}, param={"status": 2}, type='$set',
                 listback=False)
        delete(database['dbname'], database['dbuser'], database['dbpassword'], 'surveys', {"viewid": viewid},
               listback=False)
        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], {"viewid": viewid})
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("delete_one_survey", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def check_deleted_survey(payload: dict, service: RightCareServices, logger: Logger) -> tuple:
    try:
        viewid: str = payload['viewid']
        publickey: str = payload['publickey']
        apisid: str = payload['apisid']
        sessionid: str = payload['sessionid']
        alias: str = payload['alias']
        logger.info(f'viewid = {viewid} | publickey = {publickey} | apisid = {apisid} | sessionid = {sessionid}')
        codes: list = []
        # Case to check if a current survey is connected on rightcare/rightdesk
        state: bool = service.check_survey_is_configured(viewid,
                                                         dict(publickey=publickey, apisid=apisid, sessionid=sessionid))

        logger.info(f'state = {state}')

        if state: codes.append(407)

        # Case to check if a current survey is connected on salesforce or Dynamic 365
        status, code = check_survey_assigned(viewid,
                                             dict(publickey=publickey, apisid=apisid, sessionid=sessionid, alias=alias),
                                             logger)

        if status: codes.extend(code)

        if len(codes) > 0:
            logger.info(f'codes = {codes}')
            return True, hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"],
                                     {'code': codes})

        return True, hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"])

    except Exception as e:
        logger.info(f'this following error was occured : {e}')
        return False, hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                  {'message': f'this following error was occured : {e}'})


# This method allow to generate single or many qrcode to published survey
def publish_survey_qrcode(jobpayload: dict, logger: Logger):
    try:
        collection = jobpayload['collection']
        database = jobpayload['database']
        viewid = jobpayload['viewid']
        template = jobpayload["template"]
        template_link = jobpayload["template_link"]
        type = jobpayload['type']
        names = jobpayload['names']

        result = get_one(database['dbname'], database['dbuser'], database['dbpassword'], 'surveys',
                         {'viewid': viewid})
        if result[1] and result[0]:
            survey = result[0]
            if survey["status"] == 1:
                # Get the published survey by viewid
                result = get_one(config["PUBLIC_DB_NAME"], config["PUBLIC_DB_USER"], config["PUBLIC_DB_PWD"],
                                 collection, {'viewid': viewid})
                # When a published survey is find
                if result[1] and result[0]:
                    publish_id = result[0]["publish_id"]
                    response = dict()
                    param = {}
                    # Case you went to generate single qrcode
                    if type == 'single':
                        template = template.replace(" ", "_")
                        logger.info(f'template => {template}')
                        url_path = '{}/qrcode/{}'.format(publish_id, template)
                        url = hp.generate_survey_fillout_link(url_path, {'subdomain': ''})
                        qr_message = hp.qrcode_generator(url, logger)
                        qrcode_settings = {
                            "type": type,
                            "template": {
                                "name": template,
                                "link": template_link,
                                "settings": {
                                    "url": url,
                                    "image": qr_message
                                }
                            }
                        }
                        param["qrcode_settings"] = qrcode_settings
                        response = {'url': url, 'image': qr_message}
                    # Case you went to generate many qrcode
                    if type == 'multiple':
                        if not names:
                            return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"],
                                               {'message': 'names list is not specified'})
                        settings = list()
                        names = [(name.replace(" ", "_")) for name in names]
                        template = template.replace(" ", "_")
                        logger.info(f'template => {template}')
                        for name in names:
                            url_path = '{}/qrcode/{}/{}'.format(publish_id, template, quote(name))
                            url = hp.generate_survey_fillout_link(url_path, {'subdomain': ''})
                            qr_message = hp.qrcode_generator(url, logger)
                            settings.append({"name": name, "url": url, "image": qr_message})

                        qrcode_settings = {
                            "type": type,
                            "template": {
                                "name": template,
                                "link": template_link,
                                "names": names,
                                "settings": settings
                            }
                        }
                        param["qrcode_settings"] = qrcode_settings
                        response = settings

                    # Update a main survey informations
                    edit_one(database=database['dbname'], username=database['dbuser'], pwd=database['dbpassword'],
                             collection='surveys',
                             criteria={'viewid': viewid}, param=param, type='$set', listback=False)

                    # Update a publish survey informations
                    edit_one(database=config["PUBLIC_DB_NAME"], username=config["PUBLIC_DB_USER"],
                             pwd=config["PUBLIC_DB_PWD"],
                             collection=collection, criteria={'publish_id': publish_id}, param=param, type='$set',
                             listback=False)

                    # Response return when all things went well
                    return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                                       response)

                # Response return when I don't find a published survey
                return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                   {"message": "Sorry you don't find the publish survey"})

            # Response return when a survey is not already published
            return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                               {"message": "This survey need to be publish before you generate qrcode"})
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("publish_survey_qrcode", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


# This method allow to save survey template
def save_publish_survey_template(jobpayload, logger):
    try:
        payload = jobpayload['payload']
        collection = jobpayload['collection']
        database = jobpayload['database']
        result = add(database['dbname'], database['dbuser'], database['dbpassword'], collection, payload,
                     listback=False)
        logger.info('template save id: %s' % result[0])
        logger.info('template save state: %s' % result[1])
        if result[0] and result[1]:
            return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"])

        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("save_publish_survey_template", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def get_publish_survey_template(jobpayload, logger):
    try:
        collection = jobpayload['collection']
        database = jobpayload['database']
        survey_id = jobpayload['survey_id']
        result = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                         {"survey_id": survey_id})
        logger.info('template save id: %s' % result[0])
        logger.info('template save state: %s' % result[1])
        if result[0] and result[1]:
            return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data=result[0])

        return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"])
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_publish_survey_template", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def save_answer_survey(jobpayload, redis_checker, redis_instance, logger, service: RightPaymentServices):
    try:
        collection = jobpayload['collection']
        payload = jobpayload["payload"]
        result = get_one(config["PUBLIC_DB_NAME"], config["PUBLIC_DB_USER"], config["PUBLIC_DB_PWD"], "surveys_publish",
                         {'viewid': payload["viewid"], "status": 1})
        if result[1] and result[0]:
            survey_info = result[0]
            key = config["FOUNDATION_REDIS_TAG"] + survey_info["publickey"]
            database = redis_checker(key, redis_instance)
            if database:
                logger.info(f"Database infos: {database}")
                database = database["data"]
                answer_date = dt.now()
                logger.info(answer_date)
                response = get_one(database['dbname'], database['dbuser'], database['dbpassword'],
                                   collection, {'viewid': payload["viewid"]})
                survey = response[0]
                qrcode_setting = survey.get("qrcode_settings")
                channel: dict = payload["channel"]

                if channel.get("template") and channel.get("template") != qrcode_setting["template"]["name"]:
                    return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                       data={"message": f"""The template with name : {channel.get(
                                           'template')} is not associate to this survey"""})

                if channel.get("name") and channel.get("name") not in qrcode_setting["template"]["names"]:
                    return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                       data={"message": f"""The label name : {channel.get(
                                           'name')} is not associate to this survey """})

                number_response = len(survey["answers"]) if "answers" in survey else 0
                logger.info(f"number of response: {number_response}")
                respondent: int = payload["respondent"] or (number_response + 1)
                param: dict = {
                    "answers": {
                        "respondent": respondent,
                        "answer": payload["answer"],
                        "duration": payload["duration"],
                        "channel": payload["channel"],
                        "answer_date": answer_date
                    }
                }
                if payload.get("version_name"):
                    param["answers"]["version_name"] = payload.get("version_name")

                result = edit_one(database=database['dbname'], username=database['dbuser'], pwd=database['dbpassword'],
                                  collection=collection, criteria={'viewid': payload['viewid']}, param=param,
                                  type='$push', listback=False)
                if result[1] and result[0]:
                    # service.update_response_count(payload['viewid'], survey_info["publickey"])
                    payload["publickey"] = survey_info["publickey"]
                    hp.integrationsHandler(payload)
                    return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"])
                return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                   data={"message": "Failed to save survey response"})
            return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                               data={"message": "Failed to get customer database information in cache"})
        return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"],
                           data={"message": "Failed to get survey informations"})
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("save_answer_survey", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def get_survey_feedback_by_periode(jobpayload, logger):
    try:
        collection = jobpayload['collection']
        database = jobpayload['database']
        viewid = jobpayload['viewid']
        periode = jobpayload['periode']
        channel = jobpayload['channel']
        label = jobpayload['label']
        version_name = jobpayload['version_name']
        survey, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                 {'viewid': viewid})
        # Case you don't find a survey by viewid
        if not (status and survey):
            return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"],
                               data={"viewid": viewid})

        # Case the survey don't contain response
        if config["SURVEY_ATTR_ANSWERS"] not in survey:
            collected_contact = get_collected_count(viewid, database)
            logger.info(f'collected_contact = {collected_contact}')
            return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                               data={"name": survey["name"], "status": survey["status"],
                                     "type": survey["type"], "total": 0, "total_periode": 0, "average_time": 0,
                                     "channels": 0, "collected_count": collected_contact})

        # Declaration of global pipeline variables
        respondents = get_survey_answers_per_version_name(survey[config["SURVEY_ATTR_ANSWERS"]], version_name, channel)
        total_response = get_total_respondent(respondents, channel, label)
        first_match: dict = {config["PIPELINE_ATTR_MATCH"]: {"viewid": viewid}}
        first_unwind: dict = {"$unwind": config["PIPELINE_ATTR_ANSWERS"]}
        second_match: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
        third_match: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
        first_group: dict = {
            config["PIPELINE_ATTR_GROUP"]: {"_id": None, "average": {"$avg": config["PIPELINE_ATTR_ANSWERS_DURATION"]}}}
        first_project: dict = {config["PIPELINE_ATTR_PROJECT"]: {"_id": 0, "average": 1}}
        second_project: dict = {config["PIPELINE_ATTR_PROJECT"]: {"_id": 0, "total": 1}}
        second_group = {config["PIPELINE_ATTR_GROUP"]: {"_id": None, "total": {"$sum": 1}}}

        if periode in ["today", "last 7 days", "last 30 days", "custom"]:
            start_date, end_date = PeriodeConverter.converter(periode, jobpayload.get("startDate", None),
                                                              jobpayload.get("endDate", None))
            if start_date and end_date: third_match[config["PIPELINE_ATTR_MATCH"]][
                config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
                '$gte': start_date, '$lte': end_date}

            if start_date and not end_date: third_match[config["PIPELINE_ATTR_MATCH"]][
                config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
                '$gte': start_date}

            if not start_date and end_date: third_match[config["PIPELINE_ATTR_MATCH"]][
                config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
                '$lte': end_date}

        # Make check about channel or sub channel selected
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = {"$exists": False}
        if channel: second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.type"] = channel
        if label: second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.name"] = label
        if version_name: second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = version_name

        # Setup of pipeline variable for queries
        pipeline_total_periode: list = [first_match, first_unwind, second_match, third_match, second_group,
                                        second_project]

        pipeline_average_duration: list = [first_match, first_unwind, second_match, first_group, first_project]

        total_periode_response, _ = execute_aggregation(database['dbname'], database['dbuser'],
                                                        database['dbpassword'], collection,
                                                        pipeline_total_periode)

        average_duration_periode, _ = execute_aggregation(database['dbname'], database['dbuser'],
                                                          database['dbpassword'], collection,
                                                          pipeline_average_duration)

        logger.info(f"total_periode_response ==> {total_periode_response}")
        logger.info(f"average_duration_periode ==> {average_duration_periode}")
        collected_count = get_collected_count(viewid, database)
        total_periode: int = total_periode_response[0]["total"] if len(total_periode_response) > 0 else 0
        average_time: float = average_duration_periode[0]["average"] if len(average_duration_periode) > 0 else 0
        qrcode_settings = survey["qrcode_settings"] if survey.get("qrcode_settings") else None
        labels: list = qrcode_settings["template"]["names"] if qrcode_settings and qrcode_settings[
            "type"] == "multiple" else []
        simple_qrcode = survey.get('simple_qrcode', False)

        if simple_qrcode and qrcode_settings and qrcode_settings["type"] == "multiple":
            labels.append('simple')

        result: dict = {
            "name": survey["name"], "status": survey["status"],
            "type": survey["type"], "total": total_response,
            "channel": channel if channel else 'all',
            "total_periode": total_periode,
            "average_time": average_time, "channels": 1 if channel else 2,
            "collected_count": collected_count,
            "labels": labels
        }

        if result['type'] == 'template':
            result['subType'] = get_survey_template_type(survey)

        logger.info(f'result ==> {result}')

        result["versions"] = survey.get("versions") if "versions" in survey else []

        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data=result)
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_survey_feedback_by_periode", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


# This method allow to get all questions for one survey
def get_existing_survey_question_list(jobpayload, logger):
    try:
        collection = jobpayload['collection']
        database = jobpayload['database']
        viewid = jobpayload['viewid']
        version_name = jobpayload['version_name']

        parent_survey = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                {'viewid': viewid})
        if not (parent_survey[1] and parent_survey[0]):
            return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"],
                               {'message': f'The survey with viewid : {viewid} is not found'})
        versionned_survey = None
        if version_name:
            query: dict = {'parent': viewid, 'version_name': version_name}
            versionned_survey = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                        query)
        if version_name and not versionned_survey:
            return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"], {
                'message': f'The version name : {version_name} of survey with viewid : {viewid} is not found'})
        question_list: list = versionned_survey[0]['questions'] if version_name else parent_survey[0]['questions']
        type: str = parent_survey[0]['type']
        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                           data={"type": type, "questions": question_list})
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_existing_survey_question_list", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


# This method allow to get all answers for one survey
def get_existing_survey_answer_list(jobpayload, logger):
    try:
        collection, database = jobpayload['collection'], jobpayload['database']
        viewid, version_name = jobpayload['viewid'], jobpayload['version_name']

        period, startDate, endDate = jobpayload.get("period", None), jobpayload.get("startDate", None), jobpayload.get(
            "endDate", None)

        survey, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                 {'viewid': viewid})

        if not status and not survey:
            return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"])

        if config["SURVEY_ATTR_ANSWERS"] not in survey:
            return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"])

        # Call method that allow to update old survey answer channel
        update_old_survey_answer_channel(survey, database, logger)

        survey, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                 {'viewid': viewid})
        simple_qrcode, answers = survey.get('simple_qrcode', False), []

        channel_answers, qrcode_settings = {"answers_web": [], "answers_qrcode": [], "answers_simple": []}, survey.get(
            "qrcode_settings")

        questions = survey[config["SURVEY_ATTR_QUESTIONS"]]
        # Check if a given survey name exit in the incoming request and filter a question list by this version name
        if version_name:
            versionned_survey, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                           {'parent': viewid, 'version_name': version_name})
            if not versionned_survey: return hp.response(config['HTTP_STATUS']["HTTP_404"],
                                                         config['ERROR_TITLES']["HTTP_404"], {
                                                             "message": f"The survey version named : {version_name} is not found"})
            questions = versionned_survey[config["SURVEY_ATTR_QUESTIONS"]]

        answers_list: list = survey[config["SURVEY_ATTR_ANSWERS"]]

        if period:
            start_date, end_date = PeriodeConverter.converter(period, startDate, endDate)
            logger.info(f"start_date = {start_date}, end_date = {end_date}")
            answers_list = get_survey_anwers(database, viewid, collection, start_date, end_date, logger)

        # Retrieve per version if it's filled or get all
        respondents: list = get_survey_answers_per_version_name(answers_list, version_name)
        for respondent in respondents:
            fill_survey_answer_details(respondent, questions, answers)
            channel = respondent["channel"]
            type = channel["type"]
            channel_key = "answers_" + type
            logger.info(f"channel_key : {channel_key}")
            channel_answers[channel_key].append(respondent)
            logger.info(f"channel_answers[channel_key] : {channel_answers[channel_key]}")
            if qrcode_settings and qrcode_settings["type"] == "multiple" and type == "qrcode":
                name = channel["name"] if channel.get('name') else 'simple'
                logger.info(f"name : {name}")
                name_key = "answers_" + type + "_" + name
                logger.info(f"name_key : {name_key}")
                channel_answers[name_key].append(respondent) if channel_answers.get(
                    name_key) else channel_answers.setdefault(name_key, [respondent])

        if qrcode_settings and qrcode_settings["type"] == "multiple":
            channel_answers["names"] = qrcode_settings["template"]["names"]
            if simple_qrcode: channel_answers["names"].append('simple')

        logger.info(f"channel_answers : {channel_answers}")
        if survey[config["SURVEY_ATTR_TYPE"]] == config["SURVEY_TYPE_NEW"]:
            data: dict = {"type": survey["type"], "status": survey["status"], "answers": list(reversed(answers)),
                          **channel_answers}
            return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data)

        if survey[config["SURVEY_ATTR_TYPE"]] == config["SURVEY_TYPE_TEMPLATE"]:
            if 'subType' not in survey or survey['subType'] == 'nps':
                detractors, passives, promoters = categorised_template_survey_answer_values(answers, qrcode_settings[
                    "type"] if qrcode_settings else None)
                data = {"type": survey["type"], "status": survey["status"], "answers": list(reversed(answers)),
                        **detractors, **passives, **promoters, **channel_answers}

            if 'subType' in survey and survey['subType'] == 'csat':
                names = channel_answers.get("names")
                logger.info(f'names = {names}')
                result = get_csat_template_answers_feedbacks(answers, logger, names)
                logger.info(f'result = {result}')
                data = {**result, "type": survey["type"], "status": survey["status"],
                        "answers": list(reversed(answers)), **channel_answers}

            if 'subType' in survey and survey['subType'] == 'ces':
                result = get_ces_template_answers_feedbacks(answers, logger, channel_answers.get("names"))
                data = {**result, "type": survey["type"], "status": survey["status"],
                        "answers": list(reversed(answers)), **channel_answers}

            return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data)

    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_existing_survey_answer_list", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def categorised_template_survey_answer_values(answers: list, type_qrcode: str) -> tuple:
    detractors, passives, promoters = {}, {}, {}
    for respondent in answers:
        channel_type = respondent["channel"]['type']
        answer = respondent[config["SURVEY_ATTR_ANSWER"]]
        if answer[0]["value"] in list(range(0, 7)):
            key_one = f"detractors_{channel_type}"
            detractors[key_one].append(respondent) if detractors.get(key_one) else detractors.setdefault(key_one,
                                                                                                         [respondent])
            detractors["detractors"].append(respondent) if detractors.get("detractors") else detractors.setdefault(
                "detractors", [respondent])
            if type_qrcode == "multiple" and respondent["channel"]['type'] == 'qrcode':
                channel_name = respondent["channel"]['name']
                key_two = f"detractors_{channel_type}_{channel_name}"
                detractors[key_two].append(respondent) if detractors.get(key_two) else detractors.setdefault(key_two, [
                    respondent])

        if answer[0]["value"] in list(range(7, 9)):
            key_one = f"passives_{channel_type}"
            passives[key_one].append(respondent) if passives.get(key_one) else passives.setdefault(key_one,
                                                                                                   [respondent])
            passives["passives"].append(respondent) if passives.get("passives") else passives.setdefault("passives",
                                                                                                         [respondent])
            if type_qrcode == "multiple" and respondent["channel"]['type'] == 'qrcode':
                channel_name = respondent["channel"]['name']
                key_two = f"passives_{channel_type}_{channel_name}"
                passives[key_two].append(respondent) if passives.get(
                    key_two) else passives.setdefault(key_two, [respondent])

        if answer[0]["value"] in list(range(9, 11)):
            key_one = f"promoters_{channel_type}"
            promoters[key_one].append(respondent) if promoters.get(
                key_one) else promoters.setdefault(
                key_one, [respondent])
            promoters["promoters"].append(respondent) if promoters.get("promoters") else promoters.setdefault(
                "promoters", [respondent])
            if type_qrcode == "multiple" and respondent["channel"]['type'] == 'qrcode':
                channel_name = respondent["channel"]['name']
                key_two = f"promoters_{channel_type}_{channel_name}"
                promoters[key_two].append(respondent) if promoters.get(
                    key_two) else promoters.setdefault(key_two, [respondent])

    return detractors, passives, promoters


def fill_survey_answer_details(respondent: dict, questions: list, data_output: list):
    for answer in respondent[config["SURVEY_ATTR_ANSWER"]]:
        question = next((item for item in questions if
                         item[config["SURVEY_ATTR_QUESTION_ID"]] == answer[config["SURVEY_ATTR_QUESTION_ID"]]), None)
        if question:
            answer["questionType"] = question["questionType"]
            answer["questionOrder"] = question["questionOrder"]
            answer["answerDetails"] = question["answerDetails"]
            answer["questionDetails"] = question["questionDetails"]

    data_output.append(respondent)


def get_survey_answers_per_version_name(answer_list: list, version_name: str = None, channel: str = None) -> list:
    if version_name and channel:
        return [answer for answer in answer_list if
                answer.get("version_name") == version_name and answer['channel']['type'] == channel]
    if not version_name and channel:
        return [answer for answer in answer_list if
                answer['channel']['type'] == channel and 'version_name' not in answer]
    if version_name and not channel:
        return [answer for answer in answer_list if answer.get("version_name") == version_name]
    return [answer for answer in answer_list if 'version_name' not in answer]


# Service which manage survey stats by type and/or questionId
def get_stats_by_survey_question(jobpayload: dict, logger: Logger):
    try:
        collection, database = jobpayload['collection'], jobpayload['database']
        viewid, questionid = jobpayload['viewid'], jobpayload['questionid']
        channel, label, version_name = jobpayload.get('channel', None), jobpayload.get('label', None), jobpayload.get(
        'version_name', None)
        periode, startDate, endDate = jobpayload.get("periode"), jobpayload.get("startDate"), jobpayload.get(
            "endDate")
        logger.info(f"periode = {periode}, startDate = {startDate} and endDate = {endDate}")
        result: tuple = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                {'viewid': viewid})
        if result[1] and result[0]:
            survey = result[0]
            type = survey["type"]
            answers_list = survey["answers"]
            if periode:
                start_date, end_date = PeriodeConverter.converter(periode, startDate, endDate)
                logger.info(f"start_date = {start_date}, end_date = {end_date}")
                answers_list = get_survey_anwers(database, viewid, collection, start_date, end_date, logger)

            respondents: list = get_survey_answers_per_version_name(answers_list, version_name, channel)
            total_respondent = get_total_respondent(respondents, channel, label)
            data = None

            parameters: dict = {"channel": channel, "label": label, "version_name": version_name, "periode": periode,
                                "startDate": startDate, "endDate": endDate}

            # Case for survey template type NPS
            if type == "template":
                template_type = get_survey_template_type(survey)
                data = get_stats_of_survey_type_template(viewid, collection, total_respondent, database, template_type,
                                                         logger, parameters)
            # Case for survey type Question Type
            if type == "new":
                versionned_survey = None

                if version_name:
                    versionned_survey, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'],
                                                   collection, {'parent': viewid, 'version_name': version_name})

                if version_name and not versionned_survey:
                    return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"],
                                       {"message": f"The survey version named : {version_name} is not found"})

                survey_questions: list = survey[config["SURVEY_ATTR_QUESTIONS"]] if not version_name else \
                    versionned_survey[config["SURVEY_ATTR_QUESTIONS"]]
                logger.info(f"Question list with details field: {survey_questions}")
                question = next((item for item in survey_questions if item["questionId"] == int(questionid)), None)
                logger.info(f"question found details : {question}")
                if not question:
                    return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"],
                                       data={"message": "The questionid not found in specified survey"})
                data = get_stats_of_survey_question_type(viewid, questionid, collection, question, total_respondent,
                                                         database, logger, parameters)
            if data:
                return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data=data)

            return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_stats_by_survey_question", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def get_report_by_format(jobpayload, logger):
    try:
        collection, database, viewid = jobpayload['collection'], jobpayload['database'], jobpayload['viewid']
        questionid, file_type, channel = jobpayload['questionid'], jobpayload['file_type'], jobpayload.get('channel',
                                                                                                           None)
        label, version_name, LANG = jobpayload.get('label', None), jobpayload.get('version_name', None), jobpayload.get(
            'lang') if 'lang' in jobpayload else 'en'
        LANG = LANG.upper()
        logger.info("Language used to generate report is : %s" % LANG)
        survey, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                 {'viewid': viewid})

        type = survey[config["SURVEY_ATTR_TYPE"]]
        period, startDate, endDate = jobpayload.get("period"), jobpayload.get("startDate", None), jobpayload.get(
            "endDate", None)
        logger.info(f"periode = {period}, startDate = {startDate} and endDate = {endDate}")

        answers: list = survey[config["SURVEY_ATTR_ANSWERS"]]

        if period:
            start_date, end_date = PeriodeConverter.converter(period, startDate, endDate)
            logger.info(f"start_date = {start_date}, end_date = {end_date}")
            answers = get_survey_anwers(database, viewid, collection, start_date, end_date, logger)

        #logger.info(f"answers list : {answers}")
        respondents: list = get_survey_answers_per_version_name(answers, version_name, channel)

        total_respondent = get_total_respondent(respondents, channel, label)

        if total_respondent == 0:
            error_msg = "There are no respondent for a selected version of survey" if version_name else "There are no respondent for survey"
            return error_msg, False

        parameters: dict = {
            "channel": channel,
            "label": label,
            "version_name": version_name,
            "periode": period,
            "startDate": startDate,
            "endDate": endDate
        }

        versionned_survey = None

        if version_name:
            versionned_survey, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                           {'parent': viewid, 'version_name': version_name})

        if version_name and not versionned_survey:
            return f"The survey version named : {version_name} is not found", False

        survey_questions: list = survey[config["SURVEY_ATTR_QUESTIONS"]] if not version_name else versionned_survey[
            config["SURVEY_ATTR_QUESTIONS"]]

        # Case for survey template type NPS
        if type == config["SURVEY_TYPE_TEMPLATE"]:
            template_type = get_survey_template_type(survey)
            data = get_stats_of_survey_type_template(viewid, collection, total_respondent, database, template_type,
                                                     logger, parameters)
            #logger.info(f"stats data = {data}")
            question = survey_questions[0][config["SURVEY_ATTR_QUESTION_DETAILS"]][config["SURVEY_ATTR_NAME"]]
            file_name = '{}_{}.{}'.format(viewid, type, file_type)
            logger.info(file_name)
            method = '{}_template_survey_{}_report_manager'.format(template_type, file_type)
            logger.info(f"export method name : {method}")
            eval(method)(data, file_name, question, respondents, LANG, logger)

        if type == config["SURVEY_TYPE_NEW"]:
            export_questions = []
            export_questions.append(
                next((item for item in survey_questions if item[config["SURVEY_ATTR_QUESTION_ID"]] == int(questionid)),
                     None)) if questionid else export_questions.extend(survey_questions)
            file_name = exporter(type_export=file_type, viewid=viewid, questions=export_questions,
                                 collection=collection,
                                 respondants=total_respondent, answers=respondents, database=database, logger=logger,
                                 LANG=LANG, parameters=parameters)
        if not file_name:
            return f"An exception occured from report generation", False

        return file_name, True
    except Exception as e:
        logger.info(f"An exception occured in get_report_by_format method with this error : {e}")
        return f"An exception occured with following details : {e}", False


# Service which manage state of published with value: open or close
def close_or_open_one_survey(jobpayload, logger):
    try:
        logger.info(jobpayload)
        collection = jobpayload['collection']
        database = jobpayload['database']
        state = jobpayload['state']
        viewid = jobpayload['viewid']

        survey, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                 {"viewid": viewid})
        if status and survey:
            if state == "open":
                edit_one(database=database['dbname'], username=database['dbuser'], pwd=database['dbpassword'],
                         collection=collection, criteria={'viewid': viewid}, param={"status": 1}, type='$set',
                         listback=False
                         )
                edit_one(database=config["PUBLIC_DB_NAME"], username=config["PUBLIC_DB_USER"],
                         pwd=config["PUBLIC_DB_PWD"], collection="surveys_publish",
                         criteria={'viewid': viewid}, param={"status": 1}, type='$set', listback=False
                         )
                return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                                   {"message": "Survey opened successfully"})
            if state == "close":
                edit_one(database=database['dbname'], username=database['dbuser'], pwd=database['dbpassword'],
                         collection=collection,
                         criteria={'viewid': viewid}, param={"status": 2}, type='$set', listback=False)
                edit_one(database=config["PUBLIC_DB_NAME"], username=config["PUBLIC_DB_USER"],
                         pwd=config["PUBLIC_DB_PWD"], collection="surveys_publish",
                         criteria={'viewid': viewid}, param={"status": 2}, type='$set', listback=False)
                return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                                   {"message": "Survey closed successfully"})
        return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"])
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("close_or_open_one_survey", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def get_stats_of_survey_type_template(viewid: str, collection: str, total_respondent: int, database: dict,
                                      template_type: str, logger: Logger, parameters: dict = {}):
    try:
        first_match: dict = {config["PIPELINE_ATTR_MATCH"]: {"viewid": viewid}}
        second_match: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
        third_match: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
        first_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: config["PIPELINE_ATTR_ANSWERS"]}
        second_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: config["PIPELINE_ATTR_ANSWERS_ANSWER"]}
        first_group: dict = {
            config["PIPELINE_ATTR_GROUP"]: {
                "_id": config["PIPELINE_ATTR_ANSWERS_ANSWER_VALUE"],
                "total": {"$sum": 1},
                "comments": {
                    config["PIPELINE_ATTR_PUSH"]: {
                        "respondent": config["PIPELINE_ATTR_ANSWERS_RESPONDENT"],
                        "comment": "$answers.answer.comment"
                    }
                }
            }
        }
        second_group: dict = {
            config["PIPELINE_ATTR_GROUP"]: {
                "_id": None,
                "average": {
                    "$avg": config["PIPELINE_ATTR_ANSWERS_DURATION"]
                }
            }
        }
        first_project: dict = {
            config["PIPELINE_ATTR_PROJECT"]: {"_id": 0, "value": "$_id", "total": 1, "comments": 1}
        }
        second_project: dict = {
            config["PIPELINE_ATTR_PROJECT"]: {"_id": 0, "average": 1}
        }

        # Filter by channel or label
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = {"$exists": False}
        if parameters.get("channel"):
            second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.type"] = parameters.get("channel")
        if parameters.get("label"):
            second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.name"] = parameters.get("label")
        if parameters.get("version_name"):
            second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = parameters.get("version_name")

        if parameters.get("periode"):
            start_date, end_date = PeriodeConverter.converter(parameters.get("periode"), parameters.get("startDate"),
                                                              parameters.get("endDate"))

            if start_date and end_date: third_match[config["PIPELINE_ATTR_MATCH"]][
                config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
                '$gte': start_date, '$lte': end_date}

            if start_date and not end_date: third_match[config["PIPELINE_ATTR_MATCH"]][
                config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
                '$gte': start_date}

            if not start_date and end_date: third_match[config["PIPELINE_ATTR_MATCH"]][
                config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
                '$lte': end_date}

        # Stats query
        stats_pipeline: list = [first_match, first_unwind, second_match, third_match, second_unwind, first_group,
                                first_project]
        stats_result, _ = execute_aggregation(database['dbname'], database['dbuser'], database['dbpassword'],
                                              collection, stats_pipeline)
        # Average query
        average_stats_pipeline = [first_match, first_unwind, second_match, third_match, second_group, second_project]
        average_stats_result, _ = execute_aggregation(database['dbname'], database['dbuser'], database['dbpassword'],
                                                      collection, average_stats_pipeline)
        if template_type == 'nps':
            data = {
                "values": {}, "percentages": {}, "nps_score": 0,
                "time_average": 0, "values_count": {}, "total_respondent": 0,
                "comments": {"0-6": [], "7-8": [], "9-10": []}
            }

            detractors = 0
            passives = 0
            promoters = 0

            values = list(range(0, 11))

            for val in values:
                data["values_count"][val] = 0

            for res in stats_result:
                if res["value"] in values:
                    data["values_count"][res["value"]] = res["total"]
                    if res["value"] in list(range(0, 7)):
                        detractors += res["total"]
                        data["comments"]["0-6"].append({res["value"]: res["comments"]})
                    if res["value"] in list(range(7, 9)):
                        passives += res["total"]
                        data["comments"]["7-8"].append({res["value"]: res["comments"]})
                    if res["value"] in list(range(9, 11)):
                        promoters += res["total"]
                        data["comments"]["9-10"].append({res["value"]: res["comments"]})

            nps_score = ((promoters - detractors) / total_respondent) * 100

            data["values"]["detractors"] = detractors
            data["values"]["passives"] = passives
            data["values"]["promoters"] = promoters
            detractors_numeric_percentage: float = (1. / total_respondent) * detractors
            data["percentages"]["detractors"] = "{0:.0%}".format(detractors_numeric_percentage)
            passives_numeric__percentage: float = (1. / total_respondent) * passives
            data["percentages"]["passives"] = "{0:.0%}".format(passives_numeric__percentage)
            promoters_numeric_percentage: float = (1. / total_respondent) * promoters
            data["percentages"]["promoters"] = "{0:.0%}".format(promoters_numeric_percentage)
            data["nps_score"] = nps_score
            data["time_average"] = average_stats_result[0]["average"] if len(
                average_stats_result) > 0 else 0
            data["total_respondent"] = total_respondent
            data["total_percentages"] = "{0:.0%}".format(
                detractors_numeric_percentage + passives_numeric__percentage + promoters_numeric_percentage)
            return data

        values = list(range(1, 6))

        data = {"values": dict((k, 0) for k in values),
                "percentages": dict((k, "{0:.0%}".format((1. / total_respondent) * 0)) for k in values),
                "comments": dict((k, []) for k in values), "average": 0, "length": len(values),
                "total_respondent": total_respondent}
        sum_of_average_values, sum_of_average_numbers, total_percentages = 0, 0, 0
        for res in stats_result:
            key = res["value"]
            if key in values:
                data["values"][int(key)] = res["total"]
                current_percentage: float = (1. / total_respondent) * res["total"]
                data["percentages"][int(key)] = "{0:.0%}".format(current_percentage)
                data["comments"][key] = res["comments"]
                sum_of_average_values += 1 * res["total"]
                sum_of_average_numbers += res["total"]
                total_percentages += current_percentage
        if template_type == 'csat':
            csat = ((data["values"][5] + data["values"][
                4]) / sum_of_average_numbers) * 100 if sum_of_average_numbers > 0 else 0
            data["csat_score"] = round(csat, 2)
        if template_type == 'ces':
            ces = ((data["values"][5] - data["values"][
                1]) / sum_of_average_numbers) * 100 if sum_of_average_numbers > 0 else 0
            data["ces_score"] = round(ces)
        data["average"] = sum_of_average_values / sum_of_average_numbers if sum_of_average_numbers > 0 else 0
        data["total_percentages"] = "{0:.0%}".format(total_percentages)
        return data
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_stats_of_survey_type_template", e))
        return None


def get_stats_of_survey_question_type(viewid, questionid, collection, question, total_respondent, database, logger,
                                      parameters: dict = {}):
    try:
        # Rating question type
        if question["questionType"] == 1:
            return rating_question_type_stats(viewid, collection, question, total_respondent, database, logger,
                                              parameters)
        # Yes or No question type
        if question["questionType"] == 2:
            return yes_no_question_type_stats(viewid, questionid, collection, total_respondent, database, logger,
                                              parameters)
        # TextField question type
        if question["questionType"] == 3:
            return textfield_question_type_stats(viewid, questionid, collection, database, logger, parameters)
        # NPS question type
        if question["questionType"] == 5:
            return template_question_type_stats(viewid, questionid, collection, total_respondent, database, logger,
                                                parameters)
        # Multiple choice question type
        if question["questionType"] == 6:
            return multiple_choice_question_type_stats(viewid, questionid, collection, question, total_respondent,
                                                       database, logger, parameters)
        # Likert scale question type
        if question["questionType"] == 7:
            return likert_scale_question_type_stats(viewid, questionid, collection, question, total_respondent,
                                                    database, logger, parameters)
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_stats_of_survey_question_type", e))
        return None


def get_question_type(question_type, type=None, number=None, LANG='EN'):
    question_type_list = {
        "EN": {
            "1": "Rating", "2": "Yes/No", "3": "Text", "5": "NPS", "6": "Multiple Choice",
            "7": "Likert Scale"
        },
        "FR": {
            "1": "Note", "2": "Oui/Non", "3": "Texte", "5": "NPS", "6": "Choix Multiple",
            "7": "Échelle de Likert"
        }
    }
    shape_type_list = {
        "EN": {
            "1": "Stars", "2": "Hearts", "3": "Flames", "4": "Emoji", "5": "Number"
        },
        "FR": {
            "1": "Etoile", "2": "Cœur", "3": "Flamme", "4": "Emoji", "5": "Numéro"
        }
    }
    multiple_choice_options = {
        "EN": {
            "1": "Single Choice", "2": "Checkboxes", "3": "Dropdown"
        },
        "FR": {
            "1": "Choix Unique", "2": "Cases À Cocher", "3": "Menu Déroulant"
        }
    }
    likert_scale_options = {
        "EN": {
            "1": "Emoji", "2": "Points"
        },
        "FR": {
            "1": "Emoji", "2": "Points"
        }
    }
    if type and type == 1:
        return question_type_list[LANG][str(question_type)] + "-" + shape_type_list[LANG][str(number)]
    if type and type == 6:
        return question_type_list[LANG][str(question_type)] + "-" + multiple_choice_options[LANG][str(number)]
    if type and type == 7:
        return question_type_list[LANG][str(question_type)] + "-" + likert_scale_options[LANG][str(number)]

    return question_type_list[LANG][str(question_type)]


def exporter(**kwargs) -> str:
    logger = kwargs.get("logger")
    LANG = kwargs.get("LANG")
    file_name = '{}_{}.{}'.format(kwargs.get("viewid"), kwargs.get("type_export"), kwargs.get("type_export"))
    logger.info(file_name)

    pdf_details_fields = (
        ('respondant', P(config["REPORT_NAME_RESPONDANT_" + LANG], styleBH)),
        ('question_type', P(config["REPORT_NAME_QUESTION_TYPE_" + LANG], styleBH)),
        ('question', P('''<b>Question</b>''', styleBH)),
        ('response', P(config["REPORT_NAME_RESPONSE_" + LANG], styleBH)),
        ('comment', P(config["REPORT_NAME_COMMENT_" + LANG], styleBH)),
        ('date', P('''<b>Date</b>''', styleBH))
    )
    xlsx_details_fields = [
        {'header': config["REPORT_LABEL_RESPONDENT_" + LANG]},
        {'header': config["REPORT_LABEL_QUESTION_TYPE_" + LANG]},
        {'header': 'Question'},
        {'header': config["REPORT_LABEL_RESPONSE_" + LANG]},
        {'header': config["REPORT_LABEL_COMMENT_" + LANG]},
        {'header': 'Date'}
    ]
    pdf_columns_widths = []
    data_output = []
    field_output = []
    question_details = {}
    logger.info(f"file_name : {file_name}")

    for question in kwargs.get("questions"):
        logger.info("questionId: " + str(
            question[config["SURVEY_ATTR_QUESTION_ID"]]) + " start get_stats_of_survey_questiontype")
        data = get_stats_of_survey_question_type(kwargs.get("viewid"), question[config["SURVEY_ATTR_QUESTION_ID"]],
                                                 kwargs.get("collection"),
                                                 question, kwargs.get("respondants"), kwargs.get("database"),
                                                 logger, kwargs.get('parameters'))
        logger.info("questionId: " + str(
            question[config["SURVEY_ATTR_QUESTION_ID"]]) + " end get_stats_of_survey_questiontype")

        if question["questionType"] == 1:
            rating_question_type_exporter(kwargs.get("type_export"), data, question, data_output, field_output,
                                          pdf_columns_widths, LANG, logger)
        if question["questionType"] == 2:
            yes_no_question_type_exporter(kwargs.get("type_export"), data, question, data_output, field_output,
                                          pdf_columns_widths, LANG)
        if question["questionType"] == 3:
            textfield_question_type_exporter(kwargs.get("type_export"), data, question, data_output, field_output,
                                             pdf_columns_widths, logger, LANG)
        if question["questionType"] == 5:
            logger.info("questionId: " + str(
                question[config["SURVEY_ATTR_QUESTION_ID"]]) + " start template_question_type_exporter")
            template_question_type_exporter(kwargs.get("type_export"), data, question, data_output, field_output,
                                            pdf_columns_widths, logger, LANG)
            logger.info("questionId: " + str(
                question[config["SURVEY_ATTR_QUESTION_ID"]]) + " end template_question_type_exporter")

        if question["questionType"] == 6:
            multiple_choice_question_type_exporter(kwargs.get("type_export"), data, question, data_output, field_output,
                                                   pdf_columns_widths, LANG)

        if question["questionType"] == 7:
            likert_scale_question_type_exporter(kwargs.get("type_export"), data, question, data_output, field_output,
                                                pdf_columns_widths, LANG)

        logger.info(f"questionId: {question[config['SURVEY_ATTR_QUESTION_ID']]} start fill_question_details")
        logger.info(f'question details initial data : {question_details}')
        fill_question_details(kwargs.get("type_export"), kwargs.get("answers"), question, question_details, LANG,
                              logger)

        logger.info(f"questionId: {question[config['SURVEY_ATTR_QUESTION_ID']]} end fill_question_details")

    logger.info("Start fill_survey_details")
    survey_details = []
    for i in question_details.keys():
        survey_details.extend(question_details[i])
    # survey_details = [question_details[i] for i in list(question_details.keys())]
    logger.info(f"End fill_survey_details : {survey_details}")

    if kwargs.get("type_export") == config["SURVEY_EXPORT_TYPE_PDF"]:
        field_output.extend([pdf_details_fields])
        logger.info(f"field_output size: {len(field_output)}")
        logger.info(f"data_output size: {len(data_output)}")
        data_output.extend([survey_details])
        logger.info(f"data_output size: {len(data_output)}")
        pdf_columns_widths.extend([[65, 60, 70, 70, 70, 65]])
        logger.info(f"pdf_columns_widths size: {len(pdf_columns_widths)}")
        lang = LANG.lower()
        doc = DataToPdf(field_output, data_output, pdf_columns_widths, lang=lang)
        doc.export(config["BASE_PATH"] + file_name, table_halign=config["PDF_TABLE_POSITION"])

    if kwargs.get("type_export") == config["SURVEY_EXPORT_TYPE_XLSX"]:
        logger.info(f"field_output: {field_output}")
        logger.info(f"data_output: {data_output}")
        doc = DataToExcel(config["BASE_PATH"] + file_name, field_output, data_output, xlsx_details_fields,
                          survey_details)
        doc.export(config["XLSX_SHEET_ONE_" + LANG], config["XLSX_SHEET_TWO_" + LANG])
    return file_name


def nps_template_survey_pdf_report_manager(data: dict, filename: str, question: dict, answers: list, LANG: str,
                                           log: Logger = None):
    pdf_data = [
        {config["REPORT_KEY_QUESTION"]: P(question, styleN),
         config["REPORT_KEY_NPS"]: P(config["REPORT_NAME_DETRACTORS_" + LANG], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(data['values']['detractors']), styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['percentages']['detractors'], styleN)},
        {config["REPORT_KEY_QUESTION"]: P(question, styleN),
         config["REPORT_KEY_NPS"]: P(config["REPORT_NAME_PASSIVES_" + LANG], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(data['values']['passives']), styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['percentages']['passives'], styleN)},
        {config["REPORT_KEY_QUESTION"]: P(question, styleN),
         config["REPORT_KEY_NPS"]: P(config["REPORT_NAME_PROMOTERS_" + LANG], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(data['values']['promoters']), styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['percentages']['promoters'], styleN)},
        {config["REPORT_KEY_QUESTION"]: None, config["REPORT_KEY_NPS"]: P('Total', styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(f"{data['total_respondent']}", styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['total_percentages'], styleN)}
    ]
    pdf_field = (
        (config["REPORT_KEY_QUESTION"], P(config["REPORT_NAME_QUESTION"], styleBH)),
        (config["REPORT_KEY_NPS"], P(config["REPORT_NAME_NPS"], styleBH)),
        (config["REPORT_KEY_NUMBER_RESPONSE"], P(config["REPORT_NAME_NUMBER_RESPONSE_" + LANG], styleBH)),
        (config["REPORT_KEY_PERCENTAGE_RESPONSE"], P(config["REPORT_NAME_PERCENTAGE_RESPONSE_" + LANG], styleBH)),
    )
    pdf_detail_field = (
        (config["REPORT_KEY_RESPONDANT"], P(config["REPORT_NAME_RESPONDANT_" + LANG], styleBH)),
        (config["REPORT_KEY_QUESTION_TYPE"], P(config["REPORT_NAME_QUESTION_TYPE_" + LANG], styleBH)),
        (config["REPORT_KEY_QUESTION"], P(config["REPORT_NAME_QUESTION"], styleBH)),
        (config["REPORT_KEY_RESPONSE"], P(config["REPORT_NAME_RESPONSE_" + LANG], styleBH)),
        (config["REPORT_KEY_COMMENT"], P(config["REPORT_NAME_COMMENT_" + LANG], styleBH)),
        (config["REPORT_KEY_DATE"], P(config["REPORT_NAME_DATE"], styleBH))
    )
    pdf_detail_data = []
    for respondent in answers:
        answer = respondent[config["SURVEY_ATTR_ANSWER"]][0]
        if answer:
            pdf_detail_data.append(
                {config["REPORT_KEY_RESPONDANT"]: P(str(respondent[config["SURVEY_ATTR_RESPONDENT"]]), styleN),
                 config["REPORT_KEY_QUESTION_TYPE"]: P("NPS", styleN),
                 config["REPORT_KEY_QUESTION"]: P(question, styleN),
                 config["REPORT_KEY_RESPONSE"]: P(str(answer[config["SURVEY_ATTR_VALUE"]]), styleN),
                 config["REPORT_KEY_COMMENT"]: P(answer[config["SURVEY_ATTR_COMMENT"]], styleN),
                 config["REPORT_KEY_DATE"]: P(
                     hp.convert_timestamp_to_str_datetime(respondent[config.get("SURVEY_ATTR_ANSWER_DATE")]), styleN)})
    lang = LANG.lower()
    doc = DataToPdf([pdf_field, pdf_detail_field], [pdf_data, pdf_detail_data],
                    [[100, 100, 100, 100], [65, 60, 70, 70, 70, 65]], lang=lang)
    doc.export(config["BASE_PATH"] + filename, table_halign=config['PDF_TABLE_POSITION'])


def csat_template_survey_pdf_report_manager(data: dict, filename: str, question: dict, answers: list, LANG: str,
                                            log: Logger = None):
    pdf_data = [
        {config["REPORT_KEY_QUESTION"]: P(question, styleN),
         'csat': P(config['REPORT_NAME_EXTREMELY_DISSATISFIED_' + LANG], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(data['values'][1]), styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['percentages'][1], styleN)},
        {config["REPORT_KEY_QUESTION"]: P(question, styleN),
         'csat': P(config['REPORT_NAME_SOMEWHAT_SATISFIED_' + LANG], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(data['values'][2]), styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['percentages'][2], styleN)},
        {config["REPORT_KEY_QUESTION"]: P(question, styleN), 'csat': P(config['REPORT_NAME_NEUTRAL_' + LANG], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(data['values'][3]), styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['percentages'][3], styleN)},
        {config["REPORT_KEY_QUESTION"]: P(question, styleN),
         'csat': P(config['REPORT_NAME_SOMEWHAT_SATISFIED_' + LANG], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(data['values'][4]), styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['percentages'][4], styleN)},
        {config["REPORT_KEY_QUESTION"]: P(question, styleN),
         'csat': P(config['REPORT_NAME_EXTREMELY_SATISFIED_' + LANG], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(data['values'][5]), styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['percentages'][5], styleN)},
        {config["REPORT_KEY_QUESTION"]: None, 'csat': P('Total', styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(f"{data['total_respondent']}", styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['total_percentages'], styleN)}
    ]
    pdf_field = (
        (config["REPORT_KEY_QUESTION"], P(config["REPORT_NAME_QUESTION"], styleBH)),
        ('csat', P('''<b>CSAT</b>''', styleBH)),
        (config["REPORT_KEY_NUMBER_RESPONSE"], P(config["REPORT_NAME_NUMBER_RESPONSE_" + LANG], styleBH)),
        (config["REPORT_KEY_PERCENTAGE_RESPONSE"], P(config["REPORT_NAME_PERCENTAGE_RESPONSE_" + LANG], styleBH)),
    )
    pdf_detail_field = (
        (config["REPORT_KEY_RESPONDANT"], P(config["REPORT_NAME_RESPONDANT_" + LANG], styleBH)),
        (config["REPORT_KEY_QUESTION_TYPE"], P(config["REPORT_NAME_QUESTION_TYPE_" + LANG], styleBH)),
        (config["REPORT_KEY_QUESTION"], P(config["REPORT_NAME_QUESTION"], styleBH)),
        (config["REPORT_KEY_RESPONSE"], P(config["REPORT_NAME_RESPONSE_" + LANG], styleBH)),
        (config["REPORT_KEY_COMMENT"], P(config["REPORT_NAME_COMMENT_" + LANG], styleBH)),
        (config["REPORT_KEY_DATE"], P(config["REPORT_NAME_DATE"], styleBH))
    )
    pdf_detail_data = []
    for respondent in answers:
        answer = respondent[config["SURVEY_ATTR_ANSWER"]][0]
        if answer:
            pdf_detail_data.append(
                {config["REPORT_KEY_RESPONDANT"]: P(str(respondent[config["SURVEY_ATTR_RESPONDENT"]]), styleN),
                 config["REPORT_KEY_QUESTION_TYPE"]: P("CSAT", styleN),
                 config["REPORT_KEY_QUESTION"]: P(question, styleN),
                 config["REPORT_KEY_RESPONSE"]: P(str(answer[config["SURVEY_ATTR_VALUE"]]), styleN),
                 config["REPORT_KEY_COMMENT"]: P(answer[config["SURVEY_ATTR_COMMENT"]], styleN),
                 config["REPORT_KEY_DATE"]: P(
                     hp.convert_timestamp_to_str_datetime(respondent[config.get("SURVEY_ATTR_ANSWER_DATE")]), styleN)})
    lang = LANG.lower()
    doc = DataToPdf([pdf_field, pdf_detail_field], [pdf_data, pdf_detail_data],
                    [[100, 100, 100, 100], [65, 60, 70, 70, 70, 65]], lang=lang)
    doc.export(config["BASE_PATH"] + filename, table_halign=config['PDF_TABLE_POSITION'])


def ces_template_survey_pdf_report_manager(data: dict, filename: str, question: dict, answers: list, LANG: str,
                                           log: Logger = None):
    pdf_data = [
        {
        config["REPORT_KEY_QUESTION"]: P(question, styleN),
         'ces': P(config['REPORT_NAME_STRONGLY_DISAGREE_' + LANG], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(data['values'][1]), styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['percentages'][1], styleN)
         },
        {config["REPORT_KEY_QUESTION"]: P(question, styleN), 'ces': P(config['REPORT_NAME_DISAGREE_' + LANG], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(data['values'][2]), styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['percentages'][2], styleN)},
        {config["REPORT_KEY_QUESTION"]: P(question, styleN),
         'ces': P(config['REPORT_NAME_NEITHER_AGREE_' + LANG], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(data['values'][3]), styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['percentages'][3], styleN)},
        {config["REPORT_KEY_QUESTION"]: P(question, styleN), 'ces': P(config['REPORT_NAME_AGREE_' + LANG], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(data['values'][4]), styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['percentages'][4], styleN)},
        {config["REPORT_KEY_QUESTION"]: P(question, styleN),
         'ces': P(config['REPORT_NAME_STRONGLY_AGREE_' + LANG], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(data['values'][5]), styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['percentages'][5], styleN)},
        {config["REPORT_KEY_QUESTION"]: None, 'ces': P('Total', styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(f"{data['total_respondent']}", styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(data['total_percentages'], styleN)}
    ]

    if log: log.info(f"pdf_data created successfully")

    pdf_field = (
        (config["REPORT_KEY_QUESTION"], P(config["REPORT_NAME_QUESTION"], styleBH)),
        ('ces', P('''<b>CES</b>''', styleBH)),
        (config["REPORT_KEY_NUMBER_RESPONSE"], P(config["REPORT_NAME_NUMBER_RESPONSE_" + LANG], styleBH)),
        (config["REPORT_KEY_PERCENTAGE_RESPONSE"], P(config["REPORT_NAME_PERCENTAGE_RESPONSE_" + LANG], styleBH)),
    )

    if log: log.info(f"pdf_field created successfully")

    pdf_detail_field = (
        (config["REPORT_KEY_RESPONDANT"], P(config["REPORT_NAME_RESPONDANT_" + LANG], styleBH)),
        (config["REPORT_KEY_QUESTION_TYPE"], P(config["REPORT_NAME_QUESTION_TYPE_" + LANG], styleBH)),
        (config["REPORT_KEY_QUESTION"], P(config["REPORT_NAME_QUESTION"], styleBH)),
        (config["REPORT_KEY_RESPONSE"], P(config["REPORT_NAME_RESPONSE_" + LANG], styleBH)),
        (config["REPORT_KEY_COMMENT"], P(config["REPORT_NAME_COMMENT_" + LANG], styleBH)),
        (config["REPORT_KEY_DATE"], P(config["REPORT_NAME_DATE"], styleBH))
    )

    if log: log.info(f"pdf_detail_field created successfully")

    pdf_detail_data = []

    if log: log.info(f"answers => {answers}")

    for respondent in answers:

        if log: log.info(f"respondent => {respondent}")

        answer = respondent[config["SURVEY_ATTR_ANSWER"]][0]

        if log: log.info(f"answer => {answer}")

        if answer:
            current_respondent = P(f'{respondent[config.get("SURVEY_ATTR_RESPONDENT")]}', styleN)
            if log: log.info(f"respondent")
            report_question_type = P("CES", styleN)
            if log: log.info(f"report_question_type")
            question_name = P(question, styleN)
            if log: log.info(f"question_name")
            respondent_answer = P(f'{answer[config.get("SURVEY_ATTR_VALUE")]}', styleN)
            if log: log.info(f"respondent_answer")
            respondent_comment = P(answer[config["SURVEY_ATTR_COMMENT"]], styleN)
            if log: log.info(f"respondent_comment")
            answer_date = hp.convert_timestamp_to_str_datetime(respondent[config.get("SURVEY_ATTR_ANSWER_DATE")])
            if log: log.info(f"answer_date => {answer_date}")
            respondent_answer_date = P(answer_date, styleN)
            if log: log.info(f"respondent_answer_date")

            pdf_detail_data.append(
                {config["REPORT_KEY_RESPONDANT"]: current_respondent,
                 config["REPORT_KEY_QUESTION_TYPE"]: report_question_type,
                 config["REPORT_KEY_QUESTION"]: question_name,
                 config["REPORT_KEY_RESPONSE"]: respondent_answer,
                 config["REPORT_KEY_COMMENT"]: respondent_comment,
                 config["REPORT_KEY_DATE"]: respondent_answer_date})

    if log: log.info(f"pdf_detail_data => {pdf_detail_data}")
    lang = LANG.lower()
    doc = DataToPdf([pdf_field, pdf_detail_field], [pdf_data, pdf_detail_data],
                    [[100, 100, 100, 100], [65, 60, 70, 70, 70, 65]], lang=lang)
    doc.export(config["BASE_PATH"] + filename, table_halign=config['PDF_TABLE_POSITION'])


def nps_template_survey_xlsx_report_manager(data: dict, filename: str, question: dict, answers: list, LANG: str,
                                            log: Logger = None):
    excel_data = [
        [question, config["REPORT_NAME_DETRACTORS_" + LANG], data['values']['detractors'],
         data['percentages']['detractors']],
        [question, config["REPORT_NAME_PASSIVES_" + LANG], data['values']['passives'], data['percentages']['passives']],
        [question, config["REPORT_NAME_PROMOTERS_" + LANG], data['values']['promoters'],
         data['percentages']['promoters']],
        [None, 'Total', data['total_respondent'], data['total_percentages']]
    ]
    excel_header = [
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION"]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_NPS"]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_NUMBER_RESPONSE_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_PERCENTAGE_RESPONSE_" + LANG]}
    ]
    excel_detail_header = [
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_RESPONDENT_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION_TYPE_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION"]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_RESPONSE_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_COMMENT_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_DATE"]}
    ]
    excel_detail_data = []
    for respondent in answers:
        answer = respondent[config["SURVEY_ATTR_ANSWER"]][0]
        if answer:
            excel_detail_data.append(
                [respondent[config["SURVEY_ATTR_RESPONDENT"]], "NPS", question, answer[config["SURVEY_ATTR_VALUE"]],
                 answer[config["SURVEY_ATTR_COMMENT"]],
                 hp.convert_timestamp_to_str_datetime(respondent[config.get("SURVEY_ATTR_ANSWER_DATE")])])
    doc = DataToExcel(config["BASE_PATH"] + filename, [excel_header], [excel_data], excel_detail_header,
                      excel_detail_data)
    doc.export(config["XLSX_SHEET_ONE_" + LANG], config["XLSX_SHEET_TWO_" + LANG])


def csat_template_survey_xlsx_report_manager(data: dict, filename: str, question: dict, answers: list, LANG: str,
                                             log: Logger = None):
    excel_data = [
        [question, config['REPORT_NAME_EXTREMELY_DISSATISFIED_' + LANG], data['values'][1], data['percentages'][1]],
        [question, config['REPORT_NAME_SOMEWHAT_SATISFIED_' + LANG], data['values'][2], data['percentages'][2]],
        [question, config['REPORT_NAME_NEUTRAL_' + LANG], data['values'][3], data['percentages'][3]],
        [question, config['REPORT_NAME_SOMEWHAT_SATISFIED_' + LANG], data['values'][4], data['percentages'][4]],
        [question, config['REPORT_NAME_EXTREMELY_SATISFIED_' + LANG], data['values'][5], data['percentages'][5]],
        [None, 'Total', data['total_respondent'], data['total_percentages']]
    ]
    excel_header = [
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION"]},
        {config["REPORT_KEY_HEADER"]: 'CSAT'},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_NUMBER_RESPONSE_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_PERCENTAGE_RESPONSE_" + LANG]}
    ]
    excel_detail_header = [
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_RESPONDENT_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION_TYPE_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION"]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_RESPONSE_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_COMMENT_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_DATE"]}
    ]
    excel_detail_data = []
    for respondent in answers:
        answer = respondent[config["SURVEY_ATTR_ANSWER"]][0]
        if answer:
            excel_detail_data.append(
                [respondent[config["SURVEY_ATTR_RESPONDENT"]], "CSAT", question, answer[config["SURVEY_ATTR_VALUE"]],
                 answer[config["SURVEY_ATTR_COMMENT"]],
                 hp.convert_timestamp_to_str_datetime(respondent[config.get("SURVEY_ATTR_ANSWER_DATE")])])
    doc = DataToExcel(config["BASE_PATH"] + filename, [excel_header], [excel_data], excel_detail_header,
                      excel_detail_data)
    doc.export(config["XLSX_SHEET_ONE_" + LANG], config["XLSX_SHEET_TWO_" + LANG])


def ces_template_survey_xlsx_report_manager(data: dict, filename: str, question: dict, answers: list, LANG: str,
                                            log: Logger = None):
    excel_data = [
        [question, config['REPORT_NAME_STRONGLY_DISAGREE_' + LANG], data['values'][1], data['percentages'][1]],
        [question, config['REPORT_NAME_DISAGREE_' + LANG], data['values'][2], data['percentages'][2]],
        [question, config['REPORT_NAME_NEITHER_AGREE_' + LANG], data['values'][3], data['percentages'][3]],
        [question, config['REPORT_NAME_AGREE_' + LANG], data['values'][4], data['percentages'][4]],
        [question, config['REPORT_NAME_STRONGLY_AGREE_' + LANG], data['values'][5], data['percentages'][5]],
        [None, 'Total', data['total_respondent'], data['total_percentages']]
    ]
    excel_header = [
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION"]},
        {config["REPORT_KEY_HEADER"]: 'CES'},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_NUMBER_RESPONSE_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_PERCENTAGE_RESPONSE_" + LANG]}
    ]
    excel_detail_header = [
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_RESPONDENT_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION_TYPE_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION"]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_RESPONSE_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_COMMENT_" + LANG]},
        {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_DATE"]}
    ]
    excel_detail_data = []
    for respondent in answers:
        answer = respondent[config["SURVEY_ATTR_ANSWER"]][0]
        if answer:
            excel_detail_data.append(
                [respondent[config["SURVEY_ATTR_RESPONDENT"]], "CES", question, answer[config["SURVEY_ATTR_VALUE"]],
                 answer[config["SURVEY_ATTR_COMMENT"]],
                 hp.convert_timestamp_to_str_datetime(respondent[config.get("SURVEY_ATTR_ANSWER_DATE")])])
    doc = DataToExcel(config["BASE_PATH"] + filename, [excel_header], [excel_data], excel_detail_header,
                      excel_detail_data)
    doc.export(config["XLSX_SHEET_ONE_" + LANG], config["XLSX_SHEET_TWO_" + LANG])


def rating_question_type_exporter(type_export: str, data: dict, question: dict, data_output: list, field_output: list,
                                  pdf_columns_widths: list, LANG: str, logger: Logger):
    pdf_columns_widths.extend([[100, 100, 100, 100]])
    field_output.extend([[{config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION"]},
                          {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_RATING_TYPE_" + LANG]},
                          {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_NUMBER_RESPONSE_" + LANG]},
                          {config["REPORT_KEY_HEADER"]: config[
                              "REPORT_LABEL_PERCENTAGE_RESPONSE_" + LANG]}]]) if type_export == \
                                                                                 config[
                                                                                     "SURVEY_EXPORT_TYPE_XLSX"] else field_output.extend(
        [((config["REPORT_KEY_QUESTION"], P(config["REPORT_NAME_QUESTION"], styleBH)),
          (config["REPORT_KEY_RATING_TYPE"], P(config["REPORT_NAME_RATING_TYPE_" + LANG], styleBH)),
          (config["REPORT_KEY_NUMBER_RESPONSE"], P(config["REPORT_NAME_NUMBER_RESPONSE_" + LANG], styleBH)),
          (config["REPORT_KEY_PERCENTAGE_RESPONSE"], P(config["REPORT_NAME_PERCENTAGE_RESPONSE_" + LANG], styleBH)))])
    logger.info("After setup of report header")

    values = list(
        range(1, question[config["SURVEY_ATTR_QUESTION_DETAILS"]][config["SURVEY_ATTR_SHAPE_COUNT"]] + 1)) if \
        question[config["SURVEY_ATTR_QUESTION_DETAILS"]][config["SURVEY_ATTR_SHAPE_TYPE"]] in [1, 2, 3] else [1, 2, 3,
                                                                                                              4, 5]
    logger.info(f"values : {values}")
    total = 0
    instance_data = []
    logger.info(f"data : {data}")
    for val in values:
        total += data['values'][val]
        logger.info(f"total : {total}")
        rating_type = config["RATING_TYPE_FORMAT"].format(str(val), config["RATING_TYPE_MATCHES"][
            str(question[config["SURVEY_ATTR_QUESTION_DETAILS"]][config["SURVEY_ATTR_SHAPE_TYPE"]])]) if \
            question[config["SURVEY_ATTR_QUESTION_DETAILS"]][config["SURVEY_ATTR_SHAPE_TYPE"]] in [1, 2, 3] else \
            config["EMOJI_MATCH_VALUES"][str(val)]
        logger.info(f"rating_type : {rating_type}")
        question_name = hp.strip_html_tag_from_string(
            question[config["SURVEY_ATTR_QUESTION_DETAILS"]][config["SURVEY_ATTR_NAME"]])
        logger.info(f"question_name : {question_name}")
        number_response = str(data['values'][val])
        logger.info(f"number_response : {number_response}")
        number_percentage = data['percentages'][val]
        logger.info(f"number_percentage : {number_percentage}")
        if type_export == config["SURVEY_EXPORT_TYPE_PDF"]:
            instance_data.append(
                {config["REPORT_KEY_QUESTION"]: P(question_name, styleN),
                 config["REPORT_KEY_RATING_TYPE"]: P(rating_type, styleN),
                 config["REPORT_KEY_NUMBER_RESPONSE"]: P(number_response, styleN),
                 config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(number_percentage, styleN)})

        if type_export == config["SURVEY_EXPORT_TYPE_XLSX"]:
            instance_data.append([question_name, rating_type, number_response, number_percentage])

    instance_data.append(
        [None, config["REPORT_NAME_TOTAL"], total, config["REPORT_NAME_PERCENTAGE_MAX"]]) if type_export == \
                                                                                             config[
                                                                                                 "SURVEY_EXPORT_TYPE_XLSX"] else instance_data.append(
        {config["REPORT_KEY_QUESTION"]: None,
         config["REPORT_KEY_RATING_TYPE"]: P(
             config["REPORT_NAME_TOTAL"], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(total),
                                                 styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(
             config["REPORT_NAME_PERCENTAGE_MAX"], styleN)})
    data_output.extend([instance_data])


def yes_no_question_type_exporter(type_export: str, data: dict, question: dict, data_output: list, field_output: list,
                                  pdf_columns_widths: list, LANG: str):
    pdf_columns_widths.extend([[100, 100, 100, 100]])
    field_output.extend([[{config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION"]},
                          {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_TEXT_" + LANG]},
                          {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_NUMBER_RESPONSE_" + LANG]},
                          {config["REPORT_KEY_HEADER"]: config[
                              "REPORT_LABEL_PERCENTAGE_RESPONSE_" + LANG]}]]) if type_export == \
                                                                                 config[
                                                                                     "SURVEY_EXPORT_TYPE_XLSX"] else field_output.extend(
        [((config["REPORT_KEY_QUESTION"], P(config["REPORT_NAME_QUESTION"], styleBH)),
          (config["REPORT_KEY_TYPE"], P(config["REPORT_NAME_TYPE_" + LANG], styleBH)),
          (config["REPORT_KEY_NUMBER_RESPONSE"], P(config["REPORT_NAME_NUMBER_RESPONSE_" + LANG], styleBH)),
          (config["REPORT_KEY_PERCENTAGE_RESPONSE"], P(config["REPORT_NAME_PERCENTAGE_RESPONSE_" + LANG], styleBH)))])
    values = [1, 2]
    values_match = {'1': 'Yes', '2': 'No'}
    total = 0
    instance_data = []
    for val in values:
        total += data['values'][val]
        question_name = hp.strip_html_tag_from_string(
            question[config["SURVEY_ATTR_QUESTION_DETAILS"]][config["SURVEY_ATTR_NAME"]])
        number_response = str(data['values'][val])
        number_percentage = data['percentages'][val]
        type_response = values_match[str(val)]

        if type_export == config["SURVEY_EXPORT_TYPE_PDF"]:
            instance_data.append(
                {config["REPORT_KEY_QUESTION"]: P(question_name, styleN),
                 config["REPORT_KEY_TYPE"]: P(type_response, styleN),
                 config["REPORT_KEY_NUMBER_RESPONSE"]: P(number_response, styleN),
                 config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(number_percentage, styleN)})

        if type_export == config["SURVEY_EXPORT_TYPE_XLSX"]:
            instance_data.append([question_name, type_response, number_response, number_percentage])

    instance_data.append(
        [None, config["REPORT_NAME_TOTAL"], total, config["REPORT_NAME_PERCENTAGE_MAX"]]) if type_export == \
                                                                                             config[
                                                                                                 "SURVEY_EXPORT_TYPE_XLSX"] else instance_data.append(
        {config["REPORT_KEY_QUESTION"]: None,
         config["REPORT_KEY_TYPE"]: P(
             config["REPORT_NAME_TOTAL"], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(total),
                                                 styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(
             config["REPORT_NAME_PERCENTAGE_MAX"], styleN)})
    data_output.extend([instance_data])


def textfield_question_type_exporter(type_export: str, data: dict, question: dict, data_output: list,
                                     field_output: list, pdf_columns_widths: list, logger, LANG: str):
    pdf_columns_widths.extend([[150, 150, 100]])
    field_output.extend([[{config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION"]},
                          {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_TEXT_" + LANG]},
                          {config["REPORT_KEY_HEADER"]: config[
                              "REPORT_LABEL_NUMBER_RESPONSE_" + LANG]}]]) if type_export == \
                                                                             config[
                                                                                 "SURVEY_EXPORT_TYPE_XLSX"] else field_output.extend(
        [((config["REPORT_KEY_QUESTION"], P(config["REPORT_NAME_QUESTION"], styleBH)),
          (config["REPORT_KEY_TEXT"], P(config["REPORT_NAME_TEXT_" + LANG], styleBH)),
          (config["REPORT_KEY_NUMBER_RESPONSE"], P(config["REPORT_NAME_NUMBER_RESPONSE_" + LANG], styleBH)))])

    question_name = hp.strip_html_tag_from_string(
        question[config["SURVEY_ATTR_QUESTION_DETAILS"]][config["SURVEY_ATTR_NAME"]])
    comments = ", ".join(x["comment"] for x in data["comments"]) if len(data["comments"]) > 0 else ""
    logger.info("comments: %s" % comments)
    size = len(data["comments"])

    if type_export == config["SURVEY_EXPORT_TYPE_PDF"]:
        data_output.extend([[{config["REPORT_KEY_QUESTION"]: P(question_name, styleN),
                              config["REPORT_KEY_TEXT"]: P(comments, styleN),
                              config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(size), styleN)}]])

    if type_export == config["SURVEY_EXPORT_TYPE_XLSX"]:
        data_output.extend([
            [
                [question_name, comments, str(size)]
            ]
        ])


def template_question_type_exporter(type_export: str, data: dict, question: dict, data_output: list,
                                    field_output: list, pdf_columns_widths: list, logger, LANG):
    pdf_columns_widths.extend([[100, 100, 100, 100]])
    field_output.extend([[{config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION"]},
                          {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_NPS"]},
                          {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_NUMBER_RESPONSE_" + LANG]},
                          {config["REPORT_KEY_HEADER"]: config[
                              "REPORT_LABEL_PERCENTAGE_RESPONSE_" + LANG]}]]) if type_export == \
                                                                                 config[
                                                                                     "SURVEY_EXPORT_TYPE_XLSX"] else field_output.extend(
        [((config["REPORT_KEY_QUESTION"], P(config["REPORT_NAME_QUESTION"], styleBH)),
          (config["REPORT_KEY_NPS"], P(config["REPORT_NAME_NPS"], styleBH)),
          (config["REPORT_KEY_NUMBER_RESPONSE"], P(config["REPORT_NAME_NUMBER_RESPONSE_" + LANG], styleBH)),
          (config["REPORT_KEY_PERCENTAGE_RESPONSE"], P(config["REPORT_NAME_PERCENTAGE_RESPONSE_" + LANG], styleBH)))])

    question_name = hp.strip_html_tag_from_string(
        question[config["SURVEY_ATTR_QUESTION_DETAILS"]][config["SURVEY_ATTR_NAME"]])
    detractors_value = str(data['values']['detractors'])
    detractors_percentage = data['percentages']['detractors']
    passives_value = str(data['values']['passives'])
    passives_percentage = data['percentages']['passives']
    promoters_value = str(data['values']['promoters'])
    promoters_percentage = data['percentages']['promoters']
    somme = str(sum([data['values']['detractors'], data['values']['passives'], data['values']['promoters']]))

    if type_export == config["SURVEY_EXPORT_TYPE_PDF"]:
        data_output.extend([[
            {
                config["REPORT_KEY_QUESTION"]: P(question_name, styleN),
                config["REPORT_KEY_NPS"]: P(config["REPORT_NAME_DETRACTORS_" + LANG], styleN),
                config["REPORT_KEY_NUMBER_RESPONSE"]: P(detractors_value, styleN),
                config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(detractors_percentage, styleN)
            },
            {
                config["REPORT_KEY_QUESTION"]: P(question_name, styleN),
                config["REPORT_KEY_NPS"]: P(config["REPORT_NAME_PASSIVES_" + LANG], styleN),
                config["REPORT_KEY_NUMBER_RESPONSE"]: P(passives_value, styleN),
                config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(passives_percentage, styleN)
            },
            {
                config["REPORT_KEY_QUESTION"]: P(question_name, styleN),
                config["REPORT_KEY_NPS"]: P(config["REPORT_NAME_PROMOTERS_" + LANG], styleN),
                config["REPORT_KEY_NUMBER_RESPONSE"]: P(promoters_value, styleN),
                config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(promoters_percentage, styleN)
            },
            {
                config["REPORT_KEY_QUESTION"]: None,
                config["REPORT_KEY_NPS"]: P(config["REPORT_NAME_TOTAL"], styleN),
                config["REPORT_KEY_NUMBER_RESPONSE"]: P(somme, styleN),
                config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(config["REPORT_NAME_PERCENTAGE_MAX"], styleN)
            }
        ]])

    if type_export == config["SURVEY_EXPORT_TYPE_XLSX"]:
        data_output.extend([
            [
                [question_name, config["REPORT_NAME_DETRACTORS_" + LANG], detractors_value, detractors_percentage],
                [question_name, config["REPORT_NAME_PASSIVES_" + LANG], passives_value, passives_percentage],
                [question_name, config["REPORT_NAME_PROMOTERS_" + LANG], promoters_value, promoters_percentage],
                [None, config["REPORT_NAME_TOTAL"], somme, config["REPORT_NAME_PERCENTAGE_MAX"]]
            ]
        ])


def multiple_choice_question_type_exporter(type_export: str, data: dict, question: dict, data_output: list,
                                           field_output: list,
                                           pdf_columns_widths: list, LANG: str):
    pdf_columns_widths.extend([[100, 100, 100, 100]])
    multiple_choice_type = ''
    if question["questionDetails"]["type"] == 1:
        multiple_choice_type = config['REPORT_LABEL_MULTIPLE_CHOICE_DROPDOWN_' + LANG] if type_export == config[
            'SURVEY_EXPORT_TYPE_XLSX'] else config['REPORT_NAME_MULTIPLE_CHOICE_DROPDOWN_' + LANG]
    if question["questionDetails"]["type"] == 2:
        multiple_choice_type = config['REPORT_LABEL_MULTIPLE_CHOICE_CHECKBOXES_' + LANG] if type_export == config[
            'SURVEY_EXPORT_TYPE_XLSX'] else config['REPORT_NAME_MULTIPLE_CHOICE_CHECKBOXES_' + LANG]
    if question["questionDetails"]["type"] == 3:
        multiple_choice_type = config['REPORT_LABEL_MULTIPLE_CHOICE_SINGLE_CHOICE_' + LANG] if type_export == config[
            'SURVEY_EXPORT_TYPE_XLSX'] else config['REPORT_NAME_MULTIPLE_CHOICE_SINGLE_CHOICE_' + LANG]

    field_output.extend([[{config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION"]},
                          {config["REPORT_KEY_HEADER"]: multiple_choice_type},
                          {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_NUMBER_RESPONSE_" + LANG]},
                          {config["REPORT_KEY_HEADER"]: config[
                              "REPORT_LABEL_PERCENTAGE_RESPONSE_" + LANG]}]]) if type_export == \
                                                                                 config[
                                                                                     "SURVEY_EXPORT_TYPE_XLSX"] else field_output.extend(
        [
            ((config["REPORT_KEY_QUESTION"], P(config["REPORT_NAME_QUESTION"], styleBH)),
             (config["REPORT_KEY_RATING_TYPE"],
              P(multiple_choice_type, styleBH)),
             (config["REPORT_KEY_NUMBER_RESPONSE"], P(config["REPORT_NAME_NUMBER_RESPONSE_" + LANG], styleBH)),
             (
                 config["REPORT_KEY_PERCENTAGE_RESPONSE"],
                 P(config["REPORT_NAME_PERCENTAGE_RESPONSE_" + LANG], styleBH)))])
    values = [item["value"] for item in question["questionDetails"]["options"]]
    if question["questionDetails"]["otherComments"]:
        values.append("Others")
    total = 0
    instance_data = []

    for val in values:
        total += data['values'][val]
        question_name = hp.strip_html_tag_from_string(
            question[config["SURVEY_ATTR_QUESTION_DETAILS"]][config["SURVEY_ATTR_NAME"]])
        number_response = str(data['values'][val])
        number_percentage = data['percentages'][val]

        if type_export == config["SURVEY_EXPORT_TYPE_PDF"]:
            instance_data.append(
                {config["REPORT_KEY_QUESTION"]: P(question_name, styleN),
                 config["REPORT_KEY_RATING_TYPE"]: P(val, styleN),
                 config["REPORT_KEY_NUMBER_RESPONSE"]: P(number_response, styleN),
                 config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(number_percentage, styleN)})

        if type_export == config["SURVEY_EXPORT_TYPE_XLSX"]:
            instance_data.append([question_name, val, number_response, number_percentage])

    instance_data.append(
        [None, config["REPORT_NAME_TOTAL"], total, config["REPORT_NAME_PERCENTAGE_MAX"]]) if type_export == \
                                                                                             config[
                                                                                                 "SURVEY_EXPORT_TYPE_XLSX"] else instance_data.append(
        {config["REPORT_KEY_QUESTION"]: None,
         config["REPORT_KEY_RATING_TYPE"]: P(
             config["REPORT_NAME_TOTAL"], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(total),
                                                 styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(
             config["REPORT_NAME_PERCENTAGE_MAX"], styleN)})
    data_output.extend([instance_data])


def likert_scale_question_type_exporter(type_export: str, data: dict, question: dict, data_output: list,
                                        field_output: list,
                                        pdf_columns_widths: list, LANG: str):
    pdf_columns_widths.extend([[100, 100, 100, 100]])
    field_output.extend([[{config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_QUESTION"]},
                          {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_LIKERT_SCALE_TYPE_" + LANG]},
                          {config["REPORT_KEY_HEADER"]: config["REPORT_LABEL_NUMBER_RESPONSE_" + LANG]},
                          {config["REPORT_KEY_HEADER"]: config[
                              "REPORT_LABEL_PERCENTAGE_RESPONSE_" + LANG]}]]) if type_export == \
                                                                                 config[
                                                                                     "SURVEY_EXPORT_TYPE_XLSX"] else field_output.extend(
        [((config["REPORT_KEY_QUESTION"], P(config["REPORT_NAME_QUESTION"], styleBH)),
          (config["REPORT_KEY_RATING_TYPE"], P(config["REPORT_NAME_LIKERT_SCALE_TYPE_" + LANG], styleBH)),
          (config["REPORT_KEY_NUMBER_RESPONSE"], P(config["REPORT_NAME_NUMBER_RESPONSE_" + LANG], styleBH)),
          (config["REPORT_KEY_PERCENTAGE_RESPONSE"], P(config["REPORT_NAME_PERCENTAGE_RESPONSE_" + LANG], styleBH)))])
    values = list(range(1, len(question["questionDetails"]["label"]) + 1))
    total = 0
    instance_data = []
    for val in values:
        total += data['values'][val]
        question_name = hp.strip_html_tag_from_string(
            question[config["SURVEY_ATTR_QUESTION_DETAILS"]][config["SURVEY_ATTR_NAME"]])
        number_response = str(data['values'][val])
        number_percentage = data['percentages'][val]
        if type_export == config["SURVEY_EXPORT_TYPE_PDF"]:
            instance_data.append({config["REPORT_KEY_QUESTION"]: P(question_name, styleN),
                                  config["REPORT_KEY_RATING_TYPE"]: P(question["questionDetails"]["label"][val - 1],
                                                                      styleN),
                                  config["REPORT_KEY_NUMBER_RESPONSE"]: P(number_response, styleN),
                                  config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(number_percentage, styleN)})

        if type_export == config["SURVEY_EXPORT_TYPE_XLSX"]:
            instance_data.append(
                [question_name, question["questionDetails"]["label"][val - 1], number_response, number_percentage])
    instance_data.append(
        [None, config["REPORT_NAME_TOTAL"], total, config["REPORT_NAME_PERCENTAGE_MAX"]]) if type_export == \
                                                                                             config[
                                                                                                 "SURVEY_EXPORT_TYPE_XLSX"] else instance_data.append(
        {config["REPORT_KEY_QUESTION"]: None,
         config["REPORT_KEY_RATING_TYPE"]: P(
             config["REPORT_NAME_TOTAL"], styleN),
         config["REPORT_KEY_NUMBER_RESPONSE"]: P(str(total),
                                                 styleN),
         config["REPORT_KEY_PERCENTAGE_RESPONSE"]: P(
             config["REPORT_NAME_PERCENTAGE_MAX"], styleN)})
    data_output.extend([instance_data])


def fill_question_details(type_export: str, answers: list, question: dict, fill_data: dict, LANG: str, logger: Logger):
    logger.info(f'answers size : {len(answers)}')
    logger.info(f'question id :  {question["questionId"]}')
    for respondent in answers:
        answer = next((item for item in respondent["answer"] if item["questionId"] == question["questionId"]), None)
        logger.info(f'answer selected : {answer}')
        if answer:
            if question["questionType"] == 1:
                question_type = get_question_type(question["questionType"], 1, question["questionDetails"]["shapeType"],
                                                  LANG=LANG)
            elif question["questionType"] == 6:
                question_type = get_question_type(question["questionType"], 6,
                                                  question["questionDetails"]["type"], LANG=LANG)
            elif question["questionType"] == 7:
                question_type = get_question_type(question["questionType"], 7,
                                                  question["questionDetails"]["shapeType"], LANG=LANG)
            else:
                question_type = get_question_type(question["questionType"], LANG=LANG)
        logger.info(f'question type : {question_type}')
        if type_export == config["SURVEY_EXPORT_TYPE_PDF"]:
            fill_data[respondent["respondent"]].extend([
                {
                    "respondant": P(str(respondent["respondent"]), styleN),
                    "question_type": P(question_type, styleN),
                    "question": P(hp.strip_html_tag_from_string(question['questionDetails']['name']), styleN),
                    "response": P(str(answer["value"]), styleN) if not isinstance(answer["value"], list) else P(
                        ", ".join(answer["value"]), styleN),
                    "comment": P(answer["comment"], styleN),
                    "date": P(hp.convert_timestamp_to_str_datetime(respondent["answer_date"]), styleN)
                }
            ]) if fill_data.get(respondent["respondent"]) else fill_data.setdefault(respondent["respondent"], [
                {
                    "respondant": P(str(respondent["respondent"]), styleN),
                    "question_type": P(question_type, styleN),
                    "question": P(hp.strip_html_tag_from_string(question['questionDetails']['name']), styleN),
                    "response": P(str(answer["value"]), styleN) if not isinstance(answer["value"], list) else P(
                        ", ".join(answer["value"]), styleN),
                    "comment": P(answer["comment"], styleN),
                    "date": P(hp.convert_timestamp_to_str_datetime(respondent["answer_date"]), styleN)
                }
            ])

        if type_export == config["SURVEY_EXPORT_TYPE_XLSX"]:
            fill_data[respondent["respondent"]].extend([
                [
                    respondent["respondent"], question_type,
                    hp.strip_html_tag_from_string(question['questionDetails']['name']),
                    answer["value"] if not isinstance(answer["value"], list) else ", ".join(answer["value"]),
                    answer["comment"], hp.convert_timestamp_to_str_datetime(respondent["answer_date"])
                ]
            ]) if fill_data.get(respondent["respondent"]) else fill_data.setdefault(respondent["respondent"],
                                                                                    [
                                                                                        [
                                                                                            respondent["respondent"],
                                                                                            question_type,
                                                                                            hp.strip_html_tag_from_string(
                                                                                                question[
                                                                                                    'questionDetails'][
                                                                                                    'name']),
                                                                                            answer[
                                                                                                "value"] if not isinstance(
                                                                                                answer["value"],
                                                                                                list) else ", ".join(
                                                                                                answer["value"]),
                                                                                            answer["comment"],
                                                                                            hp.convert_timestamp_to_str_datetime(
                                                                                                respondent[
                                                                                                    "answer_date"])
                                                                                        ]
                                                                                    ])


def rating_question_type_stats(viewid: str, collection: str, question: dict, total_respondent: int, database: dict,
                               logger: Logger, parameters: dict = {}) -> dict:
    first_match: dict = {config["PIPELINE_ATTR_MATCH"]: {"viewid": viewid}}
    first_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: config["PIPELINE_ATTR_ANSWERS"]}
    second_match: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
    second_match_prime: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
    second_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: config["PIPELINE_ATTR_ANSWERS_ANSWER"]}
    third_match: dict = {config["PIPELINE_ATTR_MATCH"]: {
        config["SURVEY_ATTR_ANSWERS_ANSWER_QUESTION_ID"]: int(question.get('questionId'))}}
    group: dict = {config["PIPELINE_ATTR_GROUP"]: {"_id": config["PIPELINE_ATTR_ANSWERS_ANSWER_VALUE"],
                                                   "total": {"$sum": 1}, "comments": {
            config["PIPELINE_ATTR_PUSH"]: {"respondent": config["PIPELINE_ATTR_ANSWERS_RESPONDENT"],
                                           "comment": "$answers.answer.comment"}}}}
    project: dict = {config["PIPELINE_ATTR_PROJECT"]: {"_id": 0, "value": "$_id", "total": 1, "comments": 1}}
    sort: dict = {"$sort": {"value": 1}}

    second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = {"$exists": False}
    if parameters.get("channel"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.type"] = parameters.get("channel")
    if parameters.get("label"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.name"] = parameters.get("label")
    if parameters.get("version_name"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = parameters.get("version_name")

    if parameters.get("periode"):
        start_date, end_date = PeriodeConverter.converter(parameters.get("periode"), parameters.get("startDate"),
                                                          parameters.get("endDate"))

        if start_date and end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$gte': start_date, '$lte': end_date}

        if start_date and not end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$gte': start_date}

        if not start_date and end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$lte': end_date}

    pipeline: list = [first_match, first_unwind, second_match, second_match_prime, second_unwind, third_match, group,
                      project, sort]
    result, _ = execute_aggregation(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                    pipeline)
    length: int = question["questionDetails"]["shapeCount"] if question["questionDetails"]["shapeCount"] else 0

    values = list(range(1, question["questionDetails"]["shapeCount"] + 1)) if isinstance(
        question["questionDetails"]["shapeCount"], int) else list([1, 2, 3, 4, 5])
    data = {
        "values": dict((k, 0) for k in values),
        "percentages": dict(
            (k, "{0:.0%}".format((1. / total_respondent) * 0)) for k in values) if total_respondent > 0 else dict(
            (k, "{0:.0%}".format(0)) for k in values),
        "comments": dict((k, []) for k in values),
        "length": length,
        "total_respondent": total_respondent
    }
    sum_of_average_values, sum_of_average_numbers = 0, 0

    for line in result:
        if line.get("value") in values:
            data["values"][line.get("value")] = line.get("total")
            data["percentages"][line.get("value")] = "{0:.0%}".format(
                (1. / total_respondent) * line.get("total")) if total_respondent > 0 else "{0:.0%}".format(0)
            data["comments"][line.get("value")] = line.get("comments")
            sum_of_average_values += line.get("value") * line.get("total")
            sum_of_average_numbers += line.get("total")
    data["average"] = sum_of_average_values / sum_of_average_numbers if sum_of_average_numbers > 0 else 0
    return data


def yes_no_question_type_stats(viewid: str, questionid: str, collection: str, total_respondent: int, database: dict,
                               logger: Logger, parameters: dict = {}) -> dict:
    first_match: dict = {config["PIPELINE_ATTR_MATCH"]: {"viewid": viewid}}
    first_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: config["PIPELINE_ATTR_ANSWERS"]}
    second_match: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
    second_match_prime: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
    second_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: config["PIPELINE_ATTR_ANSWERS_ANSWER"]}
    third_match: dict = {config["PIPELINE_ATTR_MATCH"]: {
        config["SURVEY_ATTR_ANSWERS_ANSWER_QUESTION_ID"]: int(questionid)}}
    group: dict = {config["PIPELINE_ATTR_GROUP"]: {"_id": config["PIPELINE_ATTR_ANSWERS_ANSWER_VALUE"],
                                                   "total": {"$sum": 1}, "comments": {
            config["PIPELINE_ATTR_PUSH"]: {"respondent": config["PIPELINE_ATTR_ANSWERS_RESPONDENT"],
                                           "comment": "$answers.answer.comment"}}}}
    project: dict = {config["PIPELINE_ATTR_PROJECT"]: {"_id": 0, "value": "$_id", "total": 1, "comments": 1}}
    sort: dict = {"$sort": {"value": 1}}

    second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = {"$exists": False}
    if parameters.get("channel"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.type"] = parameters.get("channel")
    if parameters.get("label"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.name"] = parameters.get("label")
    if parameters.get("version_name"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = parameters.get("version_name")

    if parameters.get("periode"):
        start_date, end_date = PeriodeConverter.converter(parameters.get("periode"), parameters.get("startDate"),
                                                          parameters.get("endDate"))

        if start_date and end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$gte': start_date, '$lte': end_date}

        if start_date and not end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$gte': start_date}

        if not start_date and end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$lte': end_date}

    pipeline: list = [first_match, first_unwind, second_match, second_match_prime, second_unwind, third_match, group,
                      project, sort]

    result, _ = execute_aggregation(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                    pipeline)
    values = [1, 2]
    data = {"values": dict((k, 0) for k in values), "percentages": dict((k, "{0:.0%}".format(0)) for k in values),
            "comments": dict((k, []) for k in values)}
    for line in result:
        if line.get("value") in values:
            data["values"][line.get("value")] = line.get("total")
            data["percentages"][line.get("value")] = "{0:.0%}".format(
                (1. / total_respondent) * line.get("total")) if total_respondent > 0 else "{0:.0%}".format(0)
            data["comments"][line.get("value")] = line.get("comments")
    return data


def textfield_question_type_stats(viewid: str, questionid: str, collection: str, database: dict, logger: Logger,
                                  parameters: dict = {}):
    first_match: dict = {config["PIPELINE_ATTR_MATCH"]: {"viewid": viewid}}
    first_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: config["PIPELINE_ATTR_ANSWERS"]}
    second_match: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
    second_match_prime: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
    second_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: config["PIPELINE_ATTR_ANSWERS_ANSWER"]}
    third_match: dict = {config["PIPELINE_ATTR_MATCH"]: {
        config["SURVEY_ATTR_ANSWERS_ANSWER_QUESTION_ID"]: int(questionid)}}
    group: dict = {config["PIPELINE_ATTR_GROUP"]: {"_id": None, "comments": {
        config["PIPELINE_ATTR_PUSH"]: {"respondent": config["PIPELINE_ATTR_ANSWERS_RESPONDENT"],
                                       "comment": config["PIPELINE_ATTR_ANSWERS_ANSWER_VALUE"]}}}}
    project: dict = {config["PIPELINE_ATTR_PROJECT"]: {"_id": 0, "comments": 1}}
    second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = {"$exists": False}
    if parameters.get("channel"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.type"] = parameters.get("channel")
    if parameters.get("label"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.name"] = parameters.get("label")
    if parameters.get("version_name"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = parameters.get("version_name")

    if parameters.get("periode"):
        start_date, end_date = PeriodeConverter.converter(parameters.get("periode"), parameters.get("startDate"),
                                                          parameters.get("endDate"))
        second_match_prime = QueryBuilder.match_query_for_date_interval(start_date, end_date,
                                                                        config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"])

    pipeline: list = [first_match, first_unwind, second_match, second_match_prime, second_unwind, third_match, group,
                      project]
    result, _ = execute_aggregation(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                    pipeline)
    data = {"comments": result[0]["comments"] if len(result) > 0 else []}

    return data


def template_question_type_stats(viewid: str, questionid: str, collection: str, total_respondent: int, database: dict,
                                 logger: Logger, parameters: dict = {}) -> dict:
    first_match: dict = {config["PIPELINE_ATTR_MATCH"]: {"viewid": viewid}}
    second_match: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
    second_match_prime: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
    third_match: dict = {
        config["PIPELINE_ATTR_MATCH"]: {config["SURVEY_ATTR_ANSWERS_ANSWER_QUESTION_ID"]: int(questionid)}}
    first_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: config["PIPELINE_ATTR_ANSWERS"]}
    second_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: config["PIPELINE_ATTR_ANSWERS_ANSWER"]}
    first_group: dict = {config["PIPELINE_ATTR_GROUP"]: {
        "_id": config["PIPELINE_ATTR_ANSWERS_ANSWER_VALUE"],
        "total": {"$sum": 1},
        "comments": {
            config["PIPELINE_ATTR_PUSH"]: {
                "respondent": config["PIPELINE_ATTR_ANSWERS_RESPONDENT"],
                "comment": "$answers.answer.comment"
            }
        }
    }
    }
    second_group: dict = {config["PIPELINE_ATTR_GROUP"]: {"_id": None, "average": {
        "$avg": config["PIPELINE_ATTR_ANSWERS_DURATION"]}}}
    first_project: dict = {config["PIPELINE_ATTR_PROJECT"]: {"_id": 0, "value": "$_id", "total": 1, "comments": 1}}
    second_project: dict = {config["PIPELINE_ATTR_PROJECT"]: {"_id": 0, "average": 1}}
    second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = {"$exists": False}
    if parameters.get("channel"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.type"] = parameters.get("channel")
    if parameters.get("label"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.name"] = parameters.get("label")
    if parameters.get("version_name"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = parameters.get("version_name")

    if parameters.get("periode"):
        start_date, end_date = PeriodeConverter.converter(parameters.get("periode"), parameters.get("startDate"),
                                                          parameters.get("endDate"))

        if start_date and end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$gte': start_date, '$lte': end_date}

        if start_date and not end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$gte': start_date}

        if not start_date and end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$lte': end_date}

    stats_pipeline: list = [first_match, first_unwind, second_match, second_match_prime, second_unwind, third_match,
                            first_group,
                            first_project]
    stats_result, _ = execute_aggregation(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                          stats_pipeline)

    average_stats_pipeline = [first_match, first_unwind, second_match, second_match_prime, second_unwind, third_match,
                              second_group,
                              second_project]
    average_stats_result, _ = execute_aggregation(database['dbname'], database['dbuser'], database['dbpassword'],
                                                  collection, average_stats_pipeline)

    data = {
        "values": {}, "percentages": {}, "nps_score": 0,
        "time_average": 0, "values_count": {}, "total_respondent": 0,
        "comments": {"0-6": [], "7-8": [], "9-10": []}
    }

    detractors = 0
    passives = 0
    promoters = 0

    values = list(range(0, 11))

    for val in values:
        data["values_count"][val] = 0

    for res in stats_result:
        if res["value"] in values:
            data["values_count"][res["value"]] = res["total"]
            if res["value"] in list(range(0, 7)):
                detractors += res["total"]
                data["comments"]["0-6"].append({res["value"]: res["comments"]})
            if res["value"] in list(range(7, 9)):
                passives += res["total"]
                data["comments"]["7-8"].append({res["value"]: res["comments"]})
            if res["value"] in list(range(9, 11)):
                promoters += res["total"]
                data["comments"]["9-10"].append({res["value"]: res["comments"]})

    nps_score = ((promoters - detractors) / total_respondent) * 100 if total_respondent > 0 else 0
    data["values"]["detractors"] = detractors
    data["values"]["passives"] = passives
    data["values"]["promoters"] = promoters
    data["percentages"]["detractors"] = "{0:.0%}".format(
        (1. / total_respondent) * detractors) if total_respondent > 0 else "{0:.0%}".format(0)
    data["percentages"]["passives"] = "{0:.0%}".format(
        (1. / total_respondent) * passives) if total_respondent > 0 else "{0:.0%}".format(0)
    data["percentages"]["promoters"] = "{0:.0%}".format(
        (1. / total_respondent) * promoters) if total_respondent > 0 else "{0:.0%}".format(0)
    data["nps_score"] = nps_score
    data["time_average"] = average_stats_result[0]["average"] if len(
        average_stats_result) > 0 else 0
    data["total_respondent"] = total_respondent
    return data


def multiple_choice_question_type_stats(viewid: str, questionid: str, collection: str, question: dict,
                                        total_respondent: int, database: dict, logger: Logger,
                                        parameters: dict = {}) -> dict:
    first_match: dict = {config["PIPELINE_ATTR_MATCH"]: {"viewid": viewid}}
    second_match: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
    second_match_prime: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
    third_match: dict = {
        config["PIPELINE_ATTR_MATCH"]: {config["SURVEY_ATTR_ANSWERS_ANSWER_QUESTION_ID"]: int(questionid)}}
    first_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: config["PIPELINE_ATTR_ANSWERS"]}
    second_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: config["PIPELINE_ATTR_ANSWERS_ANSWER"]}
    third_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: ""}
    group: dict = {
        config["PIPELINE_ATTR_GROUP"]: {
            "_id": config["PIPELINE_ATTR_ANSWERS_ANSWER_VALUE"],
            "total": {"$sum": 1}, "comments": {
                config["PIPELINE_ATTR_PUSH"]: {
                    "respondent": config["PIPELINE_ATTR_ANSWERS_RESPONDENT"],
                    "comment": "$answers.answer.comment"
                }
            }
        }
    }
    project: dict = {config["PIPELINE_ATTR_PROJECT"]: {"_id": 0, "value": "$_id", "total": 1, "comments": 1}}
    second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = {"$exists": False}

    if parameters.get("channel"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.type"] = parameters.get("channel")
    if parameters.get("label"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.name"] = parameters.get("label")
    if parameters.get("version_name"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = parameters.get("version_name")

    if parameters.get("periode"):
        start_date, end_date = PeriodeConverter.converter(parameters.get("periode"), parameters.get("startDate"),
                                                          parameters.get("endDate"))

        if start_date and end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$gte': start_date, '$lte': end_date}

        if start_date and not end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$gte': start_date}

        if not start_date and end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$lte': end_date}

    pipeline: list = [first_match, first_unwind, second_match, second_match_prime, second_unwind, third_match, group,
                      project]

    if question["questionDetails"]["type"] == 2:
        third_unwind[config["PIPELINE_ATTR_UNWIND"]] = config["PIPELINE_ATTR_ANSWERS_ANSWER_VALUE"]
        pipeline.insert(5, third_unwind)

    stats_result, _ = execute_aggregation(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                          pipeline)
    logger.info(f"stats result : {stats_result}")
    values = [item["value"] for item in question["questionDetails"]["options"]]
    if question["questionDetails"]["otherComments"]:
        values.append("Others")
    logger.info(f"values = {values}")
    data = {"values": dict((k, 0) for k in values),
            "percentages": dict((k, "{0:.0%}".format((1. / total_respondent) * 0)) for k in values),
            "comments": dict((k, []) for k in values), "average": 0, "length": len(values),
            "total_respondent": total_respondent}
    sum_of_average_values, sum_of_average_numbers = 0, 0
    logger.info(f"Initial values for result = {data}")
    for res in stats_result:
        key = res["value"]
        logger.info(f"key = {key}")
        if key in values:
            data["values"][key] = res["total"]
            data["percentages"][key] = "{0:.0%}".format((1. / total_respondent) * res["total"])
            data["comments"][key] = res["comments"]
            sum_of_average_values += 1 * res["total"]
            sum_of_average_numbers += res["total"]
    data["average"] = sum_of_average_values / sum_of_average_numbers if sum_of_average_numbers > 0 else 0
    return data


def likert_scale_question_type_stats(viewid: str, questionid: str, collection: str, question: dict,
                                     total_respondent: int, database: dict, logger: Logger,
                                     parameters: dict = {}) -> dict:
    first_match: dict = {config["PIPELINE_ATTR_MATCH"]: {"viewid": viewid}}
    second_match: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
    second_match_prime: dict = {config["PIPELINE_ATTR_MATCH"]: {}}
    third_match: dict = {
        config["PIPELINE_ATTR_MATCH"]: {config["SURVEY_ATTR_ANSWERS_ANSWER_QUESTION_ID"]: int(questionid)}}
    first_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: config["PIPELINE_ATTR_ANSWERS"]}
    second_unwind: dict = {config["PIPELINE_ATTR_UNWIND"]: config["PIPELINE_ATTR_ANSWERS_ANSWER"]}
    group: dict = {
        config["PIPELINE_ATTR_GROUP"]: {
            "_id": config["PIPELINE_ATTR_ANSWERS_ANSWER_VALUE"],
            "total": {"$sum": 1}, "comments": {
                config["PIPELINE_ATTR_PUSH"]: {
                    "respondent": config["PIPELINE_ATTR_ANSWERS_RESPONDENT"],
                    "comment": "$answers.answer.comment"
                }
            }
        }
    }
    project: dict = {config["PIPELINE_ATTR_PROJECT"]: {"_id": 0, "value": "$_id", "total": 1, "comments": 1}}
    second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = {"$exists": False}
    if parameters.get("channel"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.type"] = parameters.get("channel")
    if parameters.get("label"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.channel.name"] = parameters.get("label")
    if parameters.get("version_name"):
        second_match[config["PIPELINE_ATTR_MATCH"]]["answers.version_name"] = parameters.get("version_name")

    if parameters.get("periode"):
        start_date, end_date = PeriodeConverter.converter(parameters.get("periode"), parameters.get("startDate"),
                                                          parameters.get("endDate"))

        if start_date and end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$gte': start_date, '$lte': end_date}

        if start_date and not end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$gte': start_date}

        if not start_date and end_date: second_match_prime[config["PIPELINE_ATTR_MATCH"]][
            config["SURVEY_ATTR_ANSWERS_ANSWER_DATE"]] = {
            '$lte': end_date}

    stats_pipeline: list = [first_match, first_unwind, second_match, second_match_prime, second_unwind, third_match, group, project]
    stats_result, _ = execute_aggregation(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                          stats_pipeline)
    values = list(range(1, len(question["questionDetails"]["label"]) + 1))
    logger.info("values = %s" % values)
    data = {
        "values": dict((k, 0) for k in values),
        "percentages": dict(
            (k, "{0:.0%}".format((1. / total_respondent) * 0)) for k in values) if total_respondent > 0 else dict(
            (k, "{0:.0%}".format(0)) for k in values),
        "comments": dict((k, []) for k in values), "average": 0, "length": len(values),
        "total_respondent": total_respondent}
    sum_of_average_values, sum_of_average_numbers = 0, 0
    for res in stats_result:
        key = res["value"]
        if key in values:
            data["values"][int(key)] = res["total"]
            data["percentages"][int(key)] = "{0:.0%}".format(
                (1. / total_respondent) * res["total"]) if total_respondent > 0 else "{0:.0%}".format(0)
            data["comments"][int(key)] = res["comments"]
            sum_of_average_values += int(res["value"]) * res["total"]
            sum_of_average_numbers += res["total"]

    if question["questionDetails"]["shapeType"] == 1:
        csat = ((data["values"][5] + data["values"][
            4]) / sum_of_average_numbers) * 100 if sum_of_average_numbers > 0 else 0
        data["csat_score"] = round(csat, 2)
    if question["questionDetails"]["shapeType"] == 2:
        ces = round((data["values"][5] / sum_of_average_numbers) * 100) - round(
            (data["values"][1] / sum_of_average_numbers) * 100) if sum_of_average_numbers > 0 else 0
        data["cse_score"] = ces
    data["average"] = sum_of_average_values / sum_of_average_numbers if sum_of_average_numbers > 0 else 0
    return data


def save_contact(jobpayload, redis_checker, redis_instance, logger):
    try:
        logger.info("jobpayload : %s" % jobpayload)
        collection = jobpayload['collection']
        payload = jobpayload["payload"]
        result = get_one(config["PUBLIC_DB_NAME"], config["PUBLIC_DB_USER"], config["PUBLIC_DB_PWD"], "surveys_publish",
                         {'viewid': payload["viewid"], "status": 1})
        logger.info("get_one result %s" % result[0])
        if result[1] and result[0]:
            survey_info = result[0]
            key = config["FOUNDATION_REDIS_TAG"] + survey_info["publickey"]
            logger.info("key : %s" % key)
            database = redis_checker(key, redis_instance)
            logger.info("database : %s" % database)
            if database:
                logger.info("database['data'] : %s" % database['data'])
                database = database["data"]
                result = check_collection_exists(database["dbname"], database["dbuser"], database["dbpassword"],
                                                 collection)
                logger.info("check_collection_exists : %s" % result[0])
                if not result[0]:
                    result = add_collection(database["dbname"], database["dbuser"], database["dbpassword"],
                                            collection)
                    logger.info("add_collection : %s" % result[0])
                result = add(database["dbname"], database["dbuser"], database["dbpassword"], collection,
                             dict(name=payload.get("name"), phone=payload.get("phone"),
                                  survey_id=payload.get("viewid")),
                             listback=False)
                logger.info("add result %s" % result[0])
                if result[1] and result[0]:
                    return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"])
                return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                                   data=dict(message="Failed to save contact"))
            return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                               data=dict(message="Failed to get customer database information in cache"))
        return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"],
                           data=dict(message="Failed to get survey informations"))
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("save_contact", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def duplicate_survey(jobpayload: dict, logger: Logger) -> str:
	try:
		collection, database, viewid = jobpayload['collection'], jobpayload['database'], jobpayload['viewid']
		survey, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
								 {'viewid': viewid})
		if status and survey:
			survey['status'] = 0
			survey['name'] += '(1)'
			del survey['viewid']
			if "answers" in survey:
				del survey['answers']
			survey['userId'] = []
			del survey['created_at']
			del survey['updated_at']
			if "qrcode_settings" in survey:
				del survey["qrcode_settings"]
			if "versions" in survey:
				last_version = survey['versions'][-1]
				last_version_survey, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'],
												 collection, {'parent': viewid, 'version_name': last_version})
				if last_version_survey:
					survey['settings'] = last_version_survey.get('settings')
					survey['questions'] = last_version_survey.get('questions')
				del survey['versions']

			survey['settings']['connectRightcare'] = False

			if "rightcareData" in survey['settings']:
				del survey['settings']['rightcareData']

			logger.info(f"duplicate survey details : {survey}")
			survey_id, status = add(database["dbname"], database["dbuser"], database["dbpassword"], collection, survey,
									listback=False)
			if status and survey_id:
				return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
								   {"viewid": survey_id})
			return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
							   {"message": "Failed to duplicate a survey with viewid : " + viewid})
		return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"])
	except Exception as e:
		logger.info(config["METHOD_ERROR_MSG"].format("duplicate_survey", e))
		return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def get_all_contacts(jobpayload: dict, logger: Logger) -> str:
    try:
        collection = jobpayload['collection']
        database = jobpayload['database']
        viewid = jobpayload['viewid']
        survey, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'], 'surveys',
                            {'viewid': viewid})

        contacts, status = get_list(database=database["dbname"], username=database["dbuser"],
                                    pwd=database["dbpassword"],
                                    collection=collection,
                                    criteria={'survey_id': viewid}, sort=[('created_date', -1)], limit=0,
                                    paginator=None)
        if status and contacts:
            return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"],
                               {'name': survey['name'], 'contacts': contacts})
        return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"])
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_all_contacts", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def export_contacts(jobpayload: dict, logger: Logger) -> tuple:
    try:
        collection = jobpayload['collection']
        database = jobpayload['database']
        viewids = jobpayload['viewids']
        survey_id = jobpayload['survey_id']
        type = jobpayload['type']

        if viewids and not survey_id:
            contacts, status = get_list(database=database["dbname"], username=database["dbuser"],
                                        pwd=database["dbpassword"],
                                        collection=collection,
                                        criteria={'viewid': {'$in': viewids}}, sort=[('created_date', -1)], limit=0,
                                        paginator=None)
        if survey_id and not viewids:
            contacts, status = get_list(database=database["dbname"], username=database["dbuser"],
                                        pwd=database["dbpassword"],
                                        collection=collection,
                                        criteria={'survey_id': survey_id}, sort=[('created_date', -1)], limit=0,
                                        paginator=None)

        if status and contacts:
            if type == config["SURVEY_EXPORT_TYPE_PDF"]:
                header_en = [
                    ('number', P('''SI. N°''', styleBH)),
                    ('name', P('''Name''', styleBH)),
                    ('phone', P('''Phone Number''', styleBH))
                ]

            if type == config["SURVEY_EXPORT_TYPE_XLSX"]:
                header_en = [{'header': 'SI. N°'}, {'header': 'Name'}, {'header': 'Phone Number'}]

            data_en = list()
            k = 0
            for contact in contacts:
                if type == config["SURVEY_EXPORT_TYPE_XLSX"]:
                    data_en.append([k + 1, contact['name'], contact['phone']])
                if type == config["SURVEY_EXPORT_TYPE_PDF"]:
                    data_en.append({'number': P(str(k + 1), styleN), 'name': P(contact['name'], styleN),
                                    'phone': P(contact['phone'], styleN)})
                k += 1
            filename = '{}.{}'.format(hp.generate_id_or_pwd(), type)
            if type == config["SURVEY_EXPORT_TYPE_XLSX"]:
                doc = DataToExcel(config["BASE_PATH"] + filename, [header_en], [data_en], [], [])
                doc.export("Contact Details")
            if type == config["SURVEY_EXPORT_TYPE_PDF"]:
                doc = DataToPdf([header_en], [data_en], [[100, 150, 150], []],
                                first_title='Collated Phone Numbers List')
                doc.export(config["BASE_PATH"] + filename, table_halign=config['PDF_TABLE_POSITION'])
            return filename, True
        return 1, False
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("export_contacts", e))
        return 2, False


def get_collected_count(viewid: str, database: dict) -> int:
    try:
        contacts, status = get_list(database=database["dbname"], username=database["dbuser"],
                                    pwd=database["dbpassword"],
                                    collection='contacts',
                                    criteria={'survey_id': viewid}, sort=[('created_date', -1)], limit=0,
                                    paginator=None)
        if status and contacts:
            return len(contacts)
        return 0
    except Exception:
        return 0


def get_csat_template_answers_feedbacks(answers: list, logger: Logger, labels: list = None) -> dict:
    logger.info(f'answers ==> {answers}')
    values: list = [1, 2, 3, 4, 5]
    comments: dict = {}
    total: dict = {}
    data: dict = {}
    sum_of_average: dict = {}
    csat: dict = {}
    logger.info('start of first step')
    total["total_respondent"] = get_total_respondent(answers)
    logger.info(f'global total respondent ==> {total["total_respondent"]}')
    total["total_respondent_web"] = get_total_respondent(answers, channel='web')
    logger.info(f'total respondent on web channel ==> {total["total_respondent_web"]}')
    total["total_respondent_qrcode"] = get_total_respondent(answers, channel='qrcode')
    logger.info(f'total respondent on qrcode channel ==> {total["total_respondent_qrcode"]}')
    comments["comments"] = {1: [], 2: [], 3: [], 4: [], 5: []}
    comments["comments_web"] = {1: [], 2: [], 3: [], 4: [], 5: []}
    comments["comments_qrcode"] = {1: [], 2: [], 3: [], 4: [], 5: []}
    data["values"] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    data["values_web"] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    data["values_qrcode"] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    data["percentages"] = dict((k, "{0:.0%}".format((1. / total["total_respondent"]) * 0)) for k in values) if total[
                                                                                                                   "total_respondent"] > 0 else dict(
        (k, "{0:.0%}".format(0)) for k in values)
    data["percentages_web"] = dict((k, "{0:.0%}".format((1. / total["total_respondent_web"]) * 0)) for k in values) if \
    total["total_respondent_web"] > 0 else dict((k, "{0:.0%}".format(0)) for k in values)
    data["percentages_qrcode"] = dict(
        (k, "{0:.0%}".format((1. / total["total_respondent_qrcode"]) * 0)) for k in values) if total[
                                                                                                   "total_respondent_qrcode"] > 0 else dict(
        (k, "{0:.0%}".format(0)) for k in values)
    sum_of_average["sum_of_average"] = 0
    sum_of_average["sum_of_average_web"] = 0
    sum_of_average["sum_of_average_qrcode"] = 0
    csat["csat_score"] = 0
    csat["csat_score_web"] = 0
    csat["csat_score_qrcode"] = 0
    logger.info('end of first step')

    logger.info('start of second step')
    if labels:
        for label in labels:
            logger.info(f'label ==> {label}')
            total["total_respondent_qrcode_" + label] = get_total_respondent(answers, channel='qrcode', label=label)
            logger.info(f'total respondent on qrcode {label} ==> {total["total_respondent_qrcode_" + label]}')
            comments["comments_qrcode_" + label] = {1: [], 2: [], 3: [], 4: [], 5: []}
            sum_of_average["sum_of_average_qrcode_" + label] = 0
            data["values_qrcode_" + label] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            data["percentages_qrcode_" + label] = dict(
                (k, "{0:.0%}".format((1. / total["total_respondent_qrcode_" + label]) * 0)) for k in values) if total[
                                                                                                                    "total_respondent_qrcode_" + label] > 0 else dict(
                (k, "{0:.0%}".format(0)) for k in values)
            csat["csat_score_qrcode_" + label] = 0
    logger.info('end of second step')

    logger.info('start of third step')
    for respondent in answers:
        answer = respondent[config["SURVEY_ATTR_ANSWER"]]
        channel = respondent["channel"]
        logger.info(f"current channel : {channel}")
        channel_type = channel.get("type")
        name = channel.get("name")
        value = answer[0]["value"]
        logger.info(f"current value : {value}")
        if value in values:
            data['values'][value] += 1
            comments["comments"][value].append(
                {"respondent": respondent["respondent"], "comment": answer[0]["comment"]})
            logger.info(f"First level data : {data} | comments : {comments}")

            logger.info(f"type of channel_type : {type(channel_type)}")
            data["values_" + channel_type][value] += 1
            comments["comments_" + channel_type][value].append(
                {"respondent": respondent["respondent"], "comment": answer[0]["comment"]})
            logger.info(f"Second level data : {data} | comments : {comments}")
            if name:
                data["values_" + channel_type + "_" + name][value] += 1
                logger.info(f"Current data : {data}")
                comments["comments_" + channel_type + "_" + name][value].append(
                    {"respondent": respondent["respondent"], "comment": answer[0]["comment"]})
                logger.info(f"Current comments : {data}")
            logger.info(f"Third level data : {data} | comments : {comments}")
    logger.info('end of third step')

    logger.info('start of fourth step')
    for value in values:
        sum_of_average["sum_of_average"] += data['values'][value]
        sum_of_average["sum_of_average_qrcode"] += data['values_qrcode'][value]
        sum_of_average["sum_of_average_web"] += data['values_web'][value]
        data["percentages"][value] = "{0:.0%}".format((1. / total["total_respondent"]) * data['values'][value]) if \
            total["total_respondent"] > 0 else "{0:.0%}".format(0)
        data["percentages_qrcode"][value] = "{0:.0%}".format(
            (1. / total["total_respondent_qrcode"]) * data['values_qrcode'][value]) if total[
                                                                                           "total_respondent_qrcode"] > 0 else "{0:.0%}".format(
            0)
        data["percentages_web"][value] = "{0:.0%}".format(
            (1. / total["total_respondent_web"]) * data['values_web'][value]) if total[
                                                                                     "total_respondent_web"] > 0 else "{0:.0%}".format(
            0)

        if labels:
            for label in labels:
                sum_of_average["sum_of_average_qrcode_" + label] += data['values_qrcode_' + label][value]
                data["percentages_qrcode_" + label][value] = "{0:.0%}".format(
                    (1. / total["total_respondent_qrcode_" + label]) * data['values_qrcode_' + label][value]) if total[
                                                                                                                     "total_respondent_qrcode_" + label] > 0 else "{0:.0%}".format(
                    0)
    logger.info('end of fourth step')

    csat["csat_score"] = round(((data["values"][5] + data["values"][4]) / sum_of_average["sum_of_average"]) * 100, 2) if \
        sum_of_average["sum_of_average"] > 0 else 0
    csat["csat_score_web"] = round(
        ((data["values_web"][5] + data["values_web"][4]) / sum_of_average["sum_of_average_web"]) * 100, 2) if \
        sum_of_average["sum_of_average_web"] > 0 else 0
    csat["csat_score_qrcode"] = round(
        ((data["values_qrcode"][5] + data["values_qrcode"][4]) / sum_of_average["sum_of_average_qrcode"]) * 100, 2) if \
        sum_of_average["sum_of_average_qrcode"] > 0 else 0
    if labels:
        for label in labels:
            csat["csat_score_qrcode_" + label] = round(
                ((data["values_qrcode_" + label][5] + data["values_qrcode_" + label][4]) / sum_of_average[
                    "sum_of_average_qrcode_" + label]) * 100, 2) if sum_of_average[
                                                                        "sum_of_average_qrcode_" + label] > 0 else 0

    logger.info(f"Last step state for csat : {csat}")

    return {**data, **csat, **comments}


def get_ces_template_answers_feedbacks(answers: list, logger: Logger, labels: list = None) -> dict:
    logger.info(f"labels : {labels}")
    values: list = [1, 2, 3, 4, 5]
    comments: dict = {}
    total: dict = {}
    data: dict = {}
    ces: dict = {}
    real_total = {}

    total["total_respondent"] = get_total_respondent(answers)
    total["total_respondent_web"] = get_total_respondent(answers, channel='web')
    logger.info(f"answers filter : {answers}")
    total["total_respondent_qrcode"] = get_total_respondent(answers, channel='qrcode')
    logger.info(f"total_respondent_qrcode : {total['total_respondent_qrcode']}")
    comments["comments"] = {1: [], 2: [], 3: [], 4: [], 5: []}
    comments["comments_web"] = {1: [], 2: [], 3: [], 4: [], 5: []}
    comments["comments_qrcode"] = {1: [], 2: [], 3: [], 4: [], 5: []}
    data["values"] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    data["values_web"] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    data["values_qrcode"] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    data["percentages"] = dict((k, "{0:.0%}".format((1. / total["total_respondent"]) * 0)) for k in values) if total[
                                                                                                                   "total_respondent"] > 0 else dict(
        (k, "{0:.0%}".format(0)) for k in values)
    data["percentages_web"] = dict((k, "{0:.0%}".format((1. / total["total_respondent_web"]) * 0)) for k in values) if \
        total["total_respondent_web"] > 0 else dict((k, "{0:.0%}".format(0)) for k in values)
    data["percentages_qrcode"] = dict(
        (k, "{0:.0%}".format((1. / total["total_respondent_qrcode"]) * 0)) for k in values) if total[
                                                                                                   "total_respondent_qrcode"] > 0 else dict(
        (k, "{0:.0%}".format(0)) for k in values)
    ces["ces_score"] = 0
    ces["ces_score_web"] = 0
    ces["ces_score_qrcode"] = 0
    real_total["real_respondent"] = 0
    real_total["real_respondent_web"] = 0
    real_total["real_respondent_qrcode"] = 0
    if labels:
        for label in labels:
            total["total_respondent_qrcode_" + label] = get_total_respondent(answers, channel='qrcode', label=label)
            comments["comments_qrcode_" + label] = {1: [], 2: [], 3: [], 4: [], 5: []}
            data["values_qrcode_" + label] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            data["percentages_qrcode_" + label] = dict(
                (k, "{0:.0%}".format((1. / total["total_respondent_qrcode_" + label]) * 0)) for k in values) if total[
                "total_respondent_qrcode_" + label] else dict((k, "{0:.0%}".format(0)) for k in values)
            ces["ces_score_qrcode_" + label] = 0
            real_total["real_respondent_qrcode_" + label] = 0
    logger.info(f"data : {data}")
    logger.info(f"labels : {labels}")
    for respondent in answers:
        answer = respondent[config["SURVEY_ATTR_ANSWER"]]
        channel = respondent["channel"]
        channel_type = channel.get("type")
        name = channel.get("name")
        value = answer[0]["value"]
        logger.info(f"channel_type : {channel_type} with name : {name} and value : {value}")
        if value in values:
            data['values'][value] += 1
            comments["comments"][value].append(
                {"respondent": respondent["respondent"], "comment": answer[0]["comment"]})
            data["values_" + channel_type][value] += 1
            comments["comments_" + channel_type][value].append(
                {"respondent": respondent["respondent"], "comment": answer[0]["comment"]})
            real_total["real_respondent"] += 1
            real_total["real_respondent_" + channel_type] += 1
            if name:
                data["values_" + channel_type + "_" + name][value] += 1
                comments["comments_" + channel_type + "_" + name][value].append(
                    {"respondent": respondent["respondent"], "comment": answer[0]["comment"]})
                real_total["real_respondent_" + channel_type + "_" + name] += 1
    logger.info(f"data : {data}")
    logger.info(f"real_total : {real_total}")
    for value in values:
        data["percentages"][value] = "{0:.0%}".format((1. / total["total_respondent"]) * data['values'][value]) if \
            total["total_respondent"] > 0 else "{0:.0%}".format(0)
        data["percentages_qrcode"][value] = "{0:.0%}".format(
            (1. / total["total_respondent_qrcode"]) * data['values_qrcode'][value]) if total[
                                                                                           "total_respondent_qrcode"] > 0 else "{0:.0%}".format(
            0)
        data["percentages_web"][value] = "{0:.0%}".format(
            (1. / total["total_respondent_web"]) * data['values_web'][value]) if total[
                                                                                     "total_respondent_web"] > 0 else "{0:.0%}".format(
            0)
        if labels:
            for label in labels:
                data["percentages_qrcode_" + label][value] = "{0:.0%}".format(
                    (1. / total["total_respondent_qrcode_" + label]) * data['values_qrcode_' + label][value]) if total[
                                                                                                                     "total_respondent_qrcode_" + label] > 0 else "{0:.0%}".format(
                    0)
    ces["ces_score"] = round(((data["values"][5] - data["values"][1]) / real_total["real_respondent"]) * 100) if \
        real_total["real_respondent"] > 0 else 0
    ces["ces_score_web"] = round(
        ((data["values_web"][5] - data["values_web"][1]) / real_total["real_respondent_web"]) * 100) if real_total[
                                                                                                            "real_respondent_web"] > 0 else 0
    ces["ces_score_qrcode"] = round(
        ((data["values_qrcode"][5] - data["values_qrcode"][1]) / real_total["real_respondent_qrcode"]) * 100) if \
        real_total["real_respondent_qrcode"] > 0 else 0
    if labels:
        for label in labels:
            ces["ces_score_qrcode_" + label] = round(
                ((data["values_qrcode_" + label][5] - data["values_qrcode_" + label][1]) / real_total[
                    "real_respondent_qrcode_" + label]) * 100) if real_total[
                                                                      "real_respondent_qrcode_" + label] > 0 else 0

    return {**data, **ces, **comments}


def get_survey_template_type(survey: dict) -> str:
    if 'subType' not in survey or survey['subType'] == 'nps':
        return 'nps'
    if 'subType' in survey and survey['subType'] == 'csat':
        return 'csat'
    if 'subType' in survey and survey['subType'] == 'ces':
        return 'ces'


# This method is used to handle the upload of csv file which new labels
def save_template_from_csvfile(jobpayload: dict, logger: Logger) -> str:
    try:
        database = jobpayload.get("database")
        collection = jobpayload.get("collection")
        payload = jobpayload.get("payload")
        viewid = payload.get("viewid")
        csvfile = payload.get("csvfile")
        bio = io.BytesIO(csvfile)
        StreamReader = codecs.getreader('utf-8')
        wrapper_file = StreamReader(bio)
        reader = csv.DictReader(wrapper_file)
        header_list = [k.replace(';', '') for k in reader.fieldnames]
        logger.info(header_list)
        rows = list(reader)
        filtered_rows = list()
        for row in rows:
            current_name = list(row.keys())[0].replace(';', '')
            current_value = list(row.values())[0].replace(';', '')
            filtered_rows.append({current_name: current_value})
        logger.info(f"content : {filtered_rows}")
        total_rows = len(filtered_rows)
        logger.info(total_rows)

        if "name" not in header_list and "Name" not in header_list:
            return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                               data=dict(message="The csv file don't contains the excepted fiels : name or Name"))
        logger.info(f"survey with viewid : {viewid}")

        if total_rows == 0:
            return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                               data=dict(message="The csv file is empty"))
        if total_rows > 50:
            return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                               data=dict(message="The csv file line numbers exceeded the maximum line require"))

        survey, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                 {'viewid': viewid})
        logger.info(f"survey with viewid : {viewid} and details : {survey}")

        if not status or not survey:
            return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"],
                               data=dict(message=f"The survey viewid : {viewid} is not found"))
        existing_labels = get_existing_labels(survey)

        for row in filtered_rows:
            name = row.get('name') or row.get('Name')
            if name not in existing_labels:
                edit_one(database=database['dbname'], username=database['dbuser'], pwd=database['dbpassword'],
                         collection=collection,
                         criteria={'viewid': viewid}, param={"template_labels": name}, type='$push', listback=False)

        survey, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], 'surveys',
                                 {'viewid': viewid})
        response = {"size": len(survey["template_labels"]), "labels": survey["template_labels"]}

        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], response)
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("save_template_from_csvfile", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def get_existing_labels(survey: dict) -> list:
    if "template_labels" in survey:
        return survey.get("template_labels")
    return list()


# This method is used to add attribute named "channel" to the old survey answer
def update_old_survey_answer_channel(survey: dict, database: dict, logger: Logger) -> None:
    first_survey_answer: dict = survey["answers"][0]
    logger.info(f"first survey answer : {first_survey_answer}")
    if not first_survey_answer.get("channel"):
        logger.info("This survey don't have a specified channel !")
        edit_many(database=database["dbname"], username=database["dbuser"], pwd=database["dbpassword"],
                  collection='surveys', criteria={"viewid": survey["viewid"]},
                  data={"$set": {"answers.$[].channel": {"type": "web", "template": "", "name": ""}}}, mult=True)
        logger.info("End of the update !")


# This method is used to update qrcode download time in timestamp
def set_download_time_to_survey(jobpayload: dict, logger: Logger) -> str:
    try:
        viewid = jobpayload.get('viewid')
        time = jobpayload.get('time')
        database = jobpayload.get('database')
        collection = jobpayload.get('collection')
        survey, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                 {'viewid': viewid})
        if not (status and survey):
            hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"],
                        {"message": f"The survey with viewid : {viewid} is not found"})
        if not survey.get('qrcode_settings'):
            hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"],
                        {"message": "You need to share survey by qrcode before update a download time of survey"})
        logger.info(f"time : {time}")
        type = '$push'
        edit_one(database=database["dbname"], username=database["dbuser"], pwd=database["dbpassword"],
                 collection=collection, criteria={'viewid': viewid}, param={"qrcode_settings.download_time": time},
                 type=type,
                 listback=False)
        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"])
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("set_download_time_to_survey", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


# This method is used to count respondent per channel or label
def get_total_respondent(answers: list, channel: str = None, label: str = None) -> int:
    if not channel and not label:
        return len(answers)

    if channel and label:
        total: int = 0
        for answer in answers:
            if answer["channel"]["type"] == channel and answer["channel"].get('name', 'simple') == label:
                total += 1
        return total

    if channel:
        total: int = 0
        for answer in answers:
            if answer["channel"]["type"] == channel:
                total += 1
        return total


def edit_survey(jobpayload: dict, logger: Logger) -> str:
    try:
        collection, payload, database = jobpayload['collection'], jobpayload['payload'], jobpayload['database']
        survey, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                 {'viewid': payload.get("parent")})
        if not (status and survey):
            return hp.response(config['HTTP_STATUS']["HTTP_404"], config['ERROR_TITLES']["HTTP_404"],
                               {"message": f"The survey parent with viewid : {payload.get('parent')}"})
        # Save new version of parent survey
        add(database["dbname"], database["dbuser"], database["dbpassword"], collection, payload, listback=False)
        # Update publish survey with the versioned survey details
        edited_param: dict = {
            "name": payload.get("name") if payload.get("name") else survey['name'],
            "version_name": payload.get("version_name"),
            "questions": payload.get("questions"),
            "settings": payload.get("settings")
        }
        publish_edit_args: dict = {
            'database': config["PUBLIC_DB_NAME"],
            'username': config["PUBLIC_DB_USER"],
            'pwd': config["PUBLIC_DB_PWD"],
            'collection': 'surveys_publish',
            'criteria': {'viewid': payload.get("parent")},
            'type': '$set',
            'listback': False,
            'param': edited_param
        }
        edit_one(**publish_edit_args)
        # Edit parent survey by version_name
        parent_survey_edit_args: dict = {
            'database': database["dbname"],
            'username': database["dbuser"],
            'pwd': database["dbpassword"],
            'collection': collection,
            'criteria': {'viewid': payload.get("parent")},
            'param': {"versions": payload.get("version_name")},
            'type': '$push',
            'listback': False
        }
        edit_one(**parent_survey_edit_args)
        if payload.get("name"):
            update_infos: dict = {
                'database': database["dbname"],
                'username': database["dbuser"],
                'pwd': database["dbpassword"],
                'collection': collection,
                'criteria': {'viewid': payload.get("parent")},
                'param': {"name": payload.get("name")},
                'type': '$set',
                'listback': False
            }
            edit_one(**update_infos)
        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"])
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("edit_survey", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])


def get_list_for_crm(database: dict, logger: Logger) -> tuple:
    try:
        logger.info(f'database : {database}')
        crm_surveys, _ = get_list(database=database["dbname"],
                                  username=database["dbuser"],
                                  pwd=database["dbpassword"],
                                  collection='surveys',
                                  criteria={
                                      'status': 1,
                                      'parent': {'$exists': False}
                                  },
                                  sort=[('created_date', -1)],
                                  projection={'viewid': 1, "name": 1, "answers": 1}
                                  )

        def crm_surveys_mapper(x: dict):
            x['total_respondent'] = len(x["answers"]) if "answers" in x else 0
            del x['_id']
            if "answers" in x: del x['answers']
            return x

        return list(map(crm_surveys_mapper, crm_surveys)), True
    except Exception as e:
        logger.info(f"An exception occured in get_list_for_crm method with this error : {e}")
        return f"An exception occured with following details : {e}", False


def get_total_respondent_for_survey(viewid: str, database: dict, logger: Logger) -> int:
    try:
        logger.info(f'viewid : {viewid}')
        logger.info(f'database : {database}')
        match: dict = {config["PIPELINE_ATTR_MATCH"]: {"viewid": viewid}}
        project: dict = {
            config["PIPELINE_ATTR_PROJECT"]: {"answers_count": {'$size': config['PIPELINE_ATTR_ANSWERS']}}
        }
        result, _ = execute_aggregation(database['dbname'], database['dbuser'], database['dbpassword'], 'surveys',
                                        [match, project])
        logger.info(f'aggregation response = {result}')
        return result[0]['answers_count']
    except Exception as e:
        logger.info(f'this following error occured : {e}')
        return 0


def get_survey_anwers(database: dict, viewid: str, collection: str, start_date, end_date, logger: Logger) -> list:
    match_query: dict = QueryBuilder.match_query_for_date_interval(start_date, end_date, "answers.answer_date")
    logger.info(f"match_query => {match_query}")
    result, status = execute_aggregation(database['dbname'], database['dbuser'], database['dbpassword'], collection,
                                         [{"$match": {"viewid": viewid}}, {"$unwind": "$answers"}, match_query,
                                          {"$group": {"_id": 0, "result": {"$push": "$answers"}}},
                                          {"$project": {"_id": 0, "result": 1}}])
    #logger.info(f"status = {status} and result = {result}")
    result = result[0]['result'] if len(result) > 0 else list()
    #logger.info(f"result => {result}")
    result = DatetimeConverter.map_datetime_to_timestamp(result)
    return result
