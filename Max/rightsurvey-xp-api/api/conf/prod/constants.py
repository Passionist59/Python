# Database mongodb configuration informations
MONGO_PRIMARY_DB_URL = "mongodb://mongo-rs-one:27017"
MONGO_SECONDARY_DB_URL = "mongodb://mongo-rs-two:27017"
MONGO_REPLICA_SET = "rs-mongo-set"

# Cache redis configuration informations
REDIS_HOST = "rs-redis"
REDIS_PORT = 6379
FOUNDATION_REDIS_TAG = "RS*"
ONBOARDING_REDIS_TAG = "RS*ON*"

# xp services base url and path
DECODER_BASE_URL = "http://xp_account_client_api:513/api"
SESSION_SERVICE = {
    "CHECK": "/decoder",
    "APPID": "app_id",
    "SID": "sid",
    "ALIAS": "alias"
}

ADMIN_BASE_URL = "http://xp_admin_api:404/api/v2/service"
ADMIN_SERVICE = {
    "VALID_SESSION": "/app_sessions/session",
    "PUBLICKEY": "publickey",
    "APISID": "apisid",
    "SESSIONID": "sessionid",
    "APPID": "appid",
    "APP_USERS": "/app_users/list",
    "CLIENT_APP_LIST": "/apps/get_client_app_list"
}

RIGHTCARE_BASE_URL = "http://10.10.25.161:715/api/v1"
RIGHTCARE_SERVICE = {
    "CREATE_CONFIG": "/rightsurvey-integration/create-configuration",
    "UPDATE_CONFIG": "/rightsurvey-integration/configuration-update",
    "DELETE_CONFIG": "/rightsurvey-integration/configuration-delete",
    "LIST_CONFIG": "/rightsurvey-integration/config-list",
    "CREATE_TICKET": "/rightsurvey-integration/create-ticket",
    "CHECK_STATE": "/rightsurvey-integration/check_survey",
    "LIST_AGENT": "/rightsurvey-integration/rightcare-plateform-agent"
}

FOUNDATION_BASE_URL = "http://xp_customer_api:5000/api"
FOUNDATION_SERVICE = {
    "CUSTOMER_DATABASE": "/get_client_product_db",
    "PUBLICKEY": "publickey",
    "PRODUCT": "product"
}

BACKEND_API = "https://rightsurveyapi.rightcom.co/api/v1/survey/daily_report?filename="
KAFKA_MAIL_SERVICE_TOPIC = "mail_service"
KAFKA_INTERNAL_BROKER_URL = "kafka1:9092,kafka2:9093,kafka3:9094"
KAFKA_INTERNAL_PRODUCER_CONFIGURATION = {'bootstrap.servers': KAFKA_INTERNAL_BROKER_URL}
MAIL_SERVICE_KEY = "AIzaSyDY0kkJiTPVd2U7a"
RIGHTSURVEY_DAILY = "RIGHTSURVEY_DAILY"

# For building of fillout survey link
SURVEY_FILLOUT_DOMAIN_BASE_URL = 'https://rightsurvey-response.rightcom.co'
SURVEY_FILLOUT_PATH = '/survey'

PAYMENT_BASE_URL = 'https://payment.rightcomtech.com/api/v1'
PAYMENT_SERVICE_PATH = {
    'LICENSE_STATUS': '/license/status'
}
