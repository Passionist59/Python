import sys

sys.path.append("/usr/src/app/api")
from core.settings import config
from utils import helpers as hp
from core.dbutils import execute_aggregation, get_one
from apscheduler.schedulers.blocking import BlockingScheduler
from services import surveys as sv
from third_party.xp_services import AccountCustomerService
from core.request_connector import HTTPJsonRequest
import json
import time
from datetime import datetime

logger = hp.get_logger(config['LOGGER']['DAILY_REPORT'], config['LOG_FILES']['DAILY_REPORT_LOG'])

redis_instance = hp.get_redis_instance()
redis_checker = hp.get_customer_database_from_redis
xp_service = AccountCustomerService(HTTPJsonRequest(), logger)


def daily_sender():

    publish_survey_per_customer_pipeline = [
        {
            config["PIPELINE_ATTR_MATCH"]: {"status": 1}
        },
        {
            config["PIPELINE_ATTR_GROUP"]: {"_id": "$publickey", "viewids": {config["PIPELINE_ATTR_PUSH"]: "$viewid"}}
        },
        {
            config["PIPELINE_ATTR_PROJECT"]: {"_id": 0, "publickey": "$_id", "viewids": 1}
        }
    ]

    publish_survey_per_customer = execute_aggregation(config["PUBLIC_DB_NAME"], config["PUBLIC_DB_USER"],
                                                      config["PUBLIC_DB_PWD"],
                                                      "surveys_publish", publish_survey_per_customer_pipeline)

    try:
        for result in publish_survey_per_customer[0]:
            logger.info(
                "*****************************************START*************************************************")
            key = config["FOUNDATION_REDIS_TAG"] + result["publickey"]
            database = redis_checker(key, redis_instance)
            database = database["data"]
            user_list = xp_service.get_account_users(result["publickey"])
            dailies = list()
            for viewid in result['viewids']:
                stats = sv.get_survey_feedback_by_periode(
                    dict(database=database, collection="surveys", viewid=viewid, periode='today'), logger)
                logger.info("stats : %s" % stats)
                if stats and "data" in stats:
                    file_name = sv.get_report_by_format(
                        dict(database=database, collection="surveys", questionid=None, file_type='pdf', viewid=viewid),
                        logger)
                    logger.info('filename : %s' % file_name)
                    stats = json.loads(stats)

                    if file_name:
                        stats["data"]["report_link"] = config["BACKEND_API"] + file_name
                        stats["data"]["average_time"] = time.strftime('%H:%M:%S',
                                                                      time.gmtime(stats["data"]["average_time"]))
                        dailies.append(stats["data"])
            logger.info("Daily data ==> %s" % dailies)
            if len(dailies) > 0:
                dailies = json.dumps(dailies)
                logger.info("Users : %s" % user_list)

                for user in user_list:
                    date_str = datetime.utcnow().strftime("%b %d, %Y") if user['language'] == 'en' else datetime.utcnow().strftime("%d %b. %Y")
                    logger.info("User : %s" % user)
                    hp.produce_to_mail_kafka(
                        {'action': config['RIGHTSURVEY_DAILY'], 'key': config['MAIL_SERVICE_KEY'], 'data': {
                            'fullname': user['firstname'] + ' ' + user['lastname']
                            , 'email': user['email'], 'report': dailies, 'date': date_str, 'language': user['language']
                        }})
                    # hp.produce_to_mail_kafka(
                    #     {'action': config['RIGHTSURVEY_DAILY'], 'key': config['MAIL_SERVICE_KEY'], 'data': {
                    #         'fullname': user['firstname'] + ' ' + user['lastname']
                    #         , 'email': 'frazeralladassi@gmail.com', 'report': dailies, 'date': date_str, 'language': user['language']
                    #     }})

            logger.info(
                "******************************************END*************************************************")
    except Exception as e:
        logger.info("Error getting is : %s" % e)

# user['language']
# daily_sender()

if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(daily_sender, 'cron', hour='19', id="daily_sender")
    try:
        scheduler.start()
        logger.info("Running")
    except (KeyboardInterrupt, SystemExit):
        pass
