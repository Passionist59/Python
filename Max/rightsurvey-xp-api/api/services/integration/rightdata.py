import sys

sys.path.append("/usr/src/app/api")
from core.dbutils import get_list, get_one, execute_aggregation
from redis import StrictRedis
from core.settings import config
from logging import Logger
from utils import helpers as hp
from datetime import datetime
import io
import csv

def link_publickey_to_rightdata_account(payload: dict, redis_instance: StrictRedis, logger: Logger) -> bool:
    status: int = 0
    try:
        account: str = payload.get("account")
        publickey: str = payload.get("publickey")
        logger.info(f"account : {account}")
        logger.info(f"publickey : {publickey}")
        status = redis_instance.hset(config['TAG_REDIS_RIGHTDATA_ACC_PUBLICKEY'], account, publickey)
        return bool(status)
    # status value will be False when this account is already set with this value
    # status value will be True when this account and value is set new
    except Exception as e:
        logger.info(f"An exception occured in link_publickey_to_rightdata_account method with this error : {e}")
        return bool(status)

def unlink_publickey_to_rightdata_account(account: str, redis_instance: StrictRedis, logger: Logger) -> bool:
    status: int = 0
    try:
        logger.info(f"account : {account}")
        status = redis_instance.hdel(config['TAG_REDIS_RIGHTDATA_ACC_PUBLICKEY'], account)
        return bool(status)
    # status value will be True, when the key is found and deleted successfully
    # status value will be False, when the key is not found and deletion failed
    except Exception as e:
        logger.info(f"An exception occured in unlink_publickey_to_rightdata_account method with this error : {e}")
        return bool(status)


def get_rightdata_account_bind_list(redis_instance: StrictRedis, logger: Logger) -> tuple:
    try:
        result = redis_instance.hgetall(config['TAG_REDIS_RIGHTDATA_ACC_PUBLICKEY'])
        logger.info(f"result : {result}")
        return hp.convert(result), True
    except Exception as e:
        logger.info(f"An exception occured in get_rightdata_account_bind_list method with this error : {e}")
        return f"An exception occured with following details : {e}", False


def get_list_of_surveys(payload: dict, redis_instance: StrictRedis, logger: Logger, redis_checker):
    try:
        collection = payload.get("collection")
        account = payload.get("account")
        if not redis_instance.hexists(config['TAG_REDIS_RIGHTDATA_ACC_PUBLICKEY'], account):
            return f"There is no RightSurvey account associated to this username", False
        publickey = redis_instance.hget(config['TAG_REDIS_RIGHTDATA_ACC_PUBLICKEY'], account)
        logger.info(f"publickey : {publickey}")
        publickey = publickey.decode('utf-8')
        key = config["FOUNDATION_REDIS_TAG"] + publickey
        result = redis_checker(key, redis_instance)
        database = result['data']
        logger.info(f"database : {database}")
        result, _ = get_list(database=database["dbname"], username=database["dbuser"], pwd=database["dbpassword"],
                             collection=collection, criteria={"parent": {"$exists": False}},
                             sort=[('created_date', -1)], projection={'viewid': 1, "name": 1,
                                                                      "description": 1, "answers": 1})
        logger.info(f'Query response : {result}')

        def survey_mapper(x: dict):
            del x['_id']
            x["total_respondent"] = len(x["answers"]) if x.get("answers") else 0
            return x

        return list(map(survey_mapper, result)), True
    except Exception as e:
        logger.info(f"An exception occured in get_list_of_surveys method with this error : {e}")
        return f"An exception occured with following details : {e}", False

def get_csv_report(payload: dict, redis_instance: StrictRedis, logger: Logger, redis_checker):
    try:
        collection = payload.get("collection")
        viewid = payload.get("viewid")
        account = payload.get("account")
        start_date, end_date = payload.get("start_date"), payload.get("end_date")
        if not redis_instance.hexists(config['TAG_REDIS_RIGHTDATA_ACC_PUBLICKEY'], account):
            return f"There is no RightSurvey account associated to this username", False
        publickey = redis_instance.hget(config['TAG_REDIS_RIGHTDATA_ACC_PUBLICKEY'], account)
        logger.info(f"publickey : {publickey}")
        publickey = publickey.decode('utf-8')
        key = config["FOUNDATION_REDIS_TAG"] + publickey
        result = redis_checker(key, redis_instance)
        database = result['data']
        logger.info(f"database : {database}")

        survey, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection, {'viewid': viewid})

        questions = survey.get('questions')
        answers = survey.get('answers')
        # 'value', 'comment', 'otherComments', 'questionName',
        fields: list = ['respondent', 'questionId', 'channel', 'answerDate', 'question_name', 'answer', 'answer_text']
        writer_file = io.StringIO()
        writer = csv.DictWriter(writer_file, fieldnames=fields)
        writer.writeheader()
        
        def get_excepted_value(question, answer):
            if question["questionType"] in [1, 2, 3, 7] and isinstance(answer["value"], int):
                labels = question["questionDetails"]["label"]
                if len(labels) <= 0:
                    return answer
                value = answer["value"]
                index = value - 1
                answer['value'] = labels[index]
                return answer
            return answer

        for question in questions:
            for respondent in answers:
                question_answers = list(
                    filter(lambda x: x["questionId"] == question["questionId"], respondent["answer"]))
                if len(question_answers) > 0:
                    question_answers = question_answers[0]
                    answer = get_excepted_value(question, question_answers)
                    questionId = answer['questionId']
                    value = ""
                    value_str = answer['value']
                    if isinstance(answer["value"], int):
                        value = answer['value']
                    comment = answer['comment']
                    otherComments = ""
                    if "otherComments" in answer:
                        otherComments = answer['otherComments']

                    answer_date = hp.convert_timestamp_to_str_datetime(respondent['answer_date'])
                    question_name: str = hp.strip_html_tag_from_string(question['questionDetails']['name'])
                    writer.writerow({"respondent": respondent["respondent"], "questionId": questionId, "channel": respondent['channel']['type'], "answerDate": answer_date, "question_name" : question_name, "answer" : value, "answer_text" : value_str})
        content = writer_file.getvalue()
        content = content.encode('utf-8')
        return content, True
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.info(f"This is the error : {e} || line ==> {exc_tb.tb_lineno}")
        logger.info(f"An exception occured in get_ticket_list method with this error : {e}")
        return f"An exception occured with following details : {e}", False
