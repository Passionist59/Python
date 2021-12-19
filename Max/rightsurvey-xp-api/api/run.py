import sys

sys.path.append("/usr/src/app/api")
import falcon
from falcon_auth import FalconAuthMiddleware
from core.settings import config
from middlewares.oauth_backend import XpOauthBackend
from core.request_connector import HTTPJsonRequest
from third_party.xp_services import AccountCustomerService
from middlewares.cors_component import CORSComponent
from middlewares.json_translator import JSONTranslator
from utils import helpers as hp
from falcon_multipart.middleware import MultipartMiddleware
from third_party.rc_services import RightCareServices
from third_party.rp_services import RightPaymentServices

# Instanciate third party class
xp_service = AccountCustomerService(HTTPJsonRequest(), hp.get_logger(config['LOGGER']['XP_SERVICES'],
                                                                     config['LOG_FILES']['XP_SERVICES_LOG']))
rc_service = RightCareServices(HTTPJsonRequest(), hp.get_logger(config['LOGGER']['RIGHTCARE_INTEGRATION_LOGGER'],
                               config['LOG_FILES']['RIGHTCARE_INTEGRATION_LOG']))
rp_logger = hp.get_logger(config['LOGGER']['RIGHTPAYMENT_INTEGRATION_LOGGER'], config['LOG_FILES']['RIGHTPAYMENT_INTEGRATION_LOG'])
rp_service = RightPaymentServices(HTTPJsonRequest(), rp_logger)

# Cache redis instanciation
redis_instance = hp.get_redis_instance()

# Security middleware setup
xp_oauth_backend = XpOauthBackend(user_loader='', service=xp_service,
                                  logger=hp.get_logger(config['LOGGER']['OAUTH_BACKEND'],
                                                       config['LOG_FILES']['OAUTH_BACKEND_LOG']),
                                  redis_instance=redis_instance, redis_checker=hp.get_customer_database_from_redis)
xp_oauth_backend_middleware = FalconAuthMiddleware(xp_oauth_backend, exempt_routes=['/v1/doc', config['BASE_ROUTE_V1'] + '/rightcare/create_ticket'])

# Falcon app setup
app_middleware = [MultipartMiddleware(), CORSComponent(), JSONTranslator(), xp_oauth_backend_middleware]
app = falcon.API(middleware=app_middleware)

import routes
import handlers
import apispec