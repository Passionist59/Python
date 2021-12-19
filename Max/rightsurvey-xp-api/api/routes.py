import sys

sys.path.append("/usr/src/app/api")
from run import app, xp_service, redis_instance, rc_service, rp_service
from core.settings import config
from utils import helpers as hp
from endpoints.v1.surveys import Surveys
from endpoints.v1.database import Databases
from endpoints.v1.session import Sessions
from endpoints.v1.on_boarding import OnBoarding
from endpoints.v1.settings import Settings
from services.on_boarding import OnBoardingService
from endpoints.v1.surveys_response import SurveysResponse
from endpoints.v1.integrations import Integrations
from endpoints.v1.integration.rightcare import RightCare
from endpoints.v1.integration.rightdata import RightData
from logging import Logger

#####
# API
#####

# Onboarding endpoint
onboarding = OnBoarding(OnBoardingService(redis_instance), hp.get_logger(config['LOGGER']['ON_BOARDING_ENDPOINT'],
                                                                         config['LOG_FILES'][
                                                                             'ON_BOARDING_ENDPOINT_LOG']))
app.add_route(config['BASE_ROUTE_V1'] + '/check_on_boarding', onboarding, suffix='check')
app.add_route(config['BASE_ROUTE_V1'] + '/update_on_boarding', onboarding, suffix='update')

# Session validation endpoint
session = Sessions(xp_service)
app.add_route(config['BASE_ROUTE_V1'] + '/decoder', session)

# Subcription endpoint
database = Databases()
app.add_route(config['BASE_ROUTE_V1'] + '/create_db', database)

# Survey management endpoint
surveys = Surveys(rc_service)
app.add_route(config['BASE_ROUTE_V1'] + '/survey', surveys)
app.add_route(config['BASE_ROUTE_V1'] + '/publish_survey/{id}', surveys, suffix='publish')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/draft', surveys, suffix='draft')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/publish_id', surveys, suffix='publish_id')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/{id}', surveys, suffix='one')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/delete/{id}', surveys)
app.add_route(config['BASE_ROUTE_V1'] + '/survey/publish_qrcode/{id}/{template}',
              surveys, suffix='publish_qrcode')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/save_publish_template', surveys, suffix='save_publish_template')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/publish_template/{id}', surveys, suffix='publish_template')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/upload_template', surveys, suffix='upload_cv_template')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/answer_feedback', surveys, suffix='survey_feedback_by_periode')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/question_list', surveys, suffix='survey_list_questions')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/answer_list', surveys, suffix='survey_list_answers')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/stats', surveys, suffix='survey_stats')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/report', surveys, suffix='survey_reports')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/close_open_survey', surveys, suffix='close_open_survey')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/predefined_list', surveys, suffix='predefined_list')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/duplicate', surveys, suffix='duplicate_survey')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/export_contact', surveys, suffix='export_contacts')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/list_contact', surveys, suffix='all_contacts')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/update_time', surveys, suffix='qrcode_download_time')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/edit', surveys, suffix='edit_survey')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/crm', surveys, suffix='crm_surveys')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/check_deletable', surveys, suffix='check_deletable')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/size', surveys, suffix='response_size')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/simple_qrcode', surveys, suffix='simple_qrcode')

# Survey global settings
settings = Settings()
app.add_route(config['BASE_ROUTE_V1'] + '/settings', settings)
app.add_route(config['BASE_ROUTE_V1'] + '/settings/welcome', settings, suffix='welcome')
app.add_route(config['BASE_ROUTE_V1'] + '/settings/logo', settings, suffix='logo')
app.add_route(config['BASE_ROUTE_V1'] + '/settings/thank_you', settings, suffix='thank_you')

# Survey response management endpoint
response_surveys = SurveysResponse(hp.get_customer_database_from_redis, redis_instance, rp_service,
                                   hp.get_logger(config['LOGGER']['RESPONSES_SURVEYS_ENDPOINT'],
                                                 config['LOG_FILES']['RESPONSES_SURVEYS_ENDPOINT_LOG']))
app.add_route(config['BASE_ROUTE_V1'] + '/survey_publish/{id}', response_surveys, suffix='publish')
app.add_route(config['BASE_ROUTE_V1'] + '/survey_publish/{id}/qrcode', response_surveys, suffix='simple_qrcode')
app.add_route(config['BASE_ROUTE_V1'] + '/survey_publish/{id}/qrcode/{template}', response_surveys,
              suffix='single_qrcode')
app.add_route(config['BASE_ROUTE_V1'] + '/survey_publish/{id}/qrcode/{template}/{name}', response_surveys,
              suffix='many_qrcode')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/answer', response_surveys, suffix='survey_answer')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/contact', response_surveys, suffix='contact')
app.add_route(config['BASE_ROUTE_V1'] + '/survey/daily_report', response_surveys, suffix='daily_report')

# Integrations endpoints
integrations = Integrations(redis_instance)
app.add_route(config['BASE_ROUTE_V1'] + '/integrations', integrations)
app.add_route(config['BASE_ROUTE_V1'] + '/integrations/salesforce', integrations, suffix="salesforce")
app.add_route(config['BASE_ROUTE_V1'] + '/integrations/microsoft', integrations, suffix="microsoft")

# Integration rightcare endpoint
rightcare = RightCare(xp_service, rc_service)
app.add_route(config['BASE_ROUTE_V1'] + '/rightcare/surveys', rightcare, suffix="survey_list")
app.add_route(config['BASE_ROUTE_V1'] + '/rightcare/agents', rightcare, suffix="rightcare_agents")
app.add_route(config['BASE_ROUTE_V1'] + '/rightcare/apps_purchased', rightcare, suffix="apps_purchased")
app.add_route(config['BASE_ROUTE_V1'] + '/rightcare/priority', rightcare, suffix="priorities")
app.add_route(config['BASE_ROUTE_V1'] + '/rightcare/create_configuration', rightcare, suffix="save_config")
app.add_route(config['BASE_ROUTE_V1'] + '/rightcare/update_configuration', rightcare, suffix="update_config")
app.add_route(config['BASE_ROUTE_V1'] + '/rightcare/delete_configuration', rightcare, suffix="remove_config")
app.add_route(config['BASE_ROUTE_V1'] + '/rightcare/connect_status', rightcare, suffix="connect_status")
app.add_route(config['BASE_ROUTE_V1'] + '/rightcare/connected_surveys', rightcare, suffix="connected_surveys")
app.add_route(config['BASE_ROUTE_V1'] + '/rightcare/disconnect', rightcare, suffix="disconnect")
app.add_route(config['BASE_ROUTE_V1'] + '/rightcare/disconnect_all', rightcare, suffix="disconnect_all")
app.add_route(config['BASE_ROUTE_V1'] + '/rightcare/create_ticket', rightcare, suffix="create_ticket")

# Integration righdata endpoint
logger: Logger = hp.get_logger(config['LOGGER']['RIGHTDATA_INTEGRATION_LOGGER'],
                               config['LOG_FILES']['RIGHTDATA_INTEGRATION_LOG'])
rightdata = RightData(logger, redis_instance, hp.get_customer_database_from_redis)
app.add_route(config['BASE_ROUTE_V1'] + '/rightdata/surveys', rightdata, suffix="surveys")
app.add_route(config['BASE_ROUTE_V1'] + '/rightdata/report', rightdata, suffix="report")
app.add_route(config['BASE_ROUTE_V1'] + '/rightdata/link', rightdata, suffix="link")
app.add_route(config['BASE_ROUTE_V1'] + '/rightdata/unlink', rightdata, suffix="unlink")
app.add_route(config['BASE_ROUTE_V1'] + '/rightdata/link_list', rightdata, suffix="bind_acc_list")

