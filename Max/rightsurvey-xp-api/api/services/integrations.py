import sys

sys.path.append("/usr/src/app/api")
from core.settings import config
from utils import helpers as hp
from core.dbutils import get_list, add, edit_one, get_one, delete, execute_aggregation, add_to_public, \
    check_collection_exists, add_collection, edit_many
from logging import Logger
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceAuthenticationFailed
import json
import msal
from utils.microsoft import Client

rs_redis = hp.get_redis_instance()

# Get all active integrations
def build_integration_status(integration, config_json, database, logger):
    try:
        if integration == "SALESFORCE":
            instance = Salesforce(username=config_json["username"], password=config_json["password"], security_token=config_json["security_token"])
            del config_json["password"]
        elif integration == "MICROSOFT":
            app = msal.ConfidentialClientApplication(config_json["client_id"], authority=config_json["authority"], client_credential=config_json["secret"])
            scope = config_json["instance_url"] + "/.default"
            result = app.acquire_token_for_client(scopes=scope)
            if result is None:
                return 0, {}
            if "access_token" not in result:
                return 0, {}
        else:
            return 0, {}
        
        if "survey" in config_json and config_json["survey"] != "":
            survey, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], "surveys", {'viewid': config_json['survey']})
            if survey and status:
                if survey is None:
                    return 1, config_json

                survey_payload = {
                    "name" : survey["name"],
                    "description" : survey["description"],
                    "status" : survey["status"],
                    "type" : survey["type"],
                    "subType" : survey["subType"] if "subType" in survey else "",
                    "answers" : len(survey["answers"]) if "answers" in survey else 0
                }
                config_json["survey_info"] = survey_payload

        return 1, config_json
    except SalesforceAuthenticationFailed as auth_error:
        logger.info(config["METHOD_ERROR_MSG"].format("get_salesforce_auth", auth_error))
        return 0, {}
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_integrations", e))
        return 0, {}

# Service that gets the list of all integrations
def get_integrations(jobpayload, redis_instance, logger):
    try:
        integrations = {}
        # Check Integrations
        for integration in config["INTEGRATIONS_IMPLEMENTED"]:
            integrations[integration] = {
                "active" : 0,
                "details" : {}
            }

            config_json = redis_instance.hget(integration + "_SURVEYS", jobpayload["publickey"])
            if config_json is not None:
                config_json = json.loads(config_json.decode("utf8").replace("”", "\""))
                integrations[integration]["active"], integrations[integration]["details"]= build_integration_status(integration, config_json, jobpayload["database"], logger)
        
        integrations["code"] = 448
        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data=integrations)
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_integrations", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], data={"code" : 449})

# Service which checks if Salesforce credentials are valid and store.
def get_salesforce_auth(jobpayload, redis_instance, logger):
    try:
        instance = Salesforce(username=jobpayload["username"], password=jobpayload["password"], security_token=jobpayload["security_token"])

        # Generate webhook URL
        b64_publickey = hp.encode_string(jobpayload["publickey"])
        webhook_url = config["WEBHOOKS"]["SALESFORCE"].format(b64_publickey)

        redis_payload = json.dumps({
            "username" : jobpayload["username"],
            "password" : jobpayload["password"],
            "security_token" : jobpayload["security_token"],
            "webhook_url" : webhook_url
        })

        # Save information to rs-redis
        redis_instance.hset(config["INTEGRATIONS_KEYS"]["SALESFORCE_SURVEYS"], jobpayload["publickey"], redis_payload)

        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data={
            "code" : 450,
            "webhook" : webhook_url
        })
    except SalesforceAuthenticationFailed as auth_error:
        logger.info(config["METHOD_ERROR_MSG"].format("get_salesforce_auth", auth_error))
        return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], error={
            "message" : "E-AUTH-SALESFORCE"
        }, data={"code" : 451})
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_salesforce_auth", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], data={"code" : 451})

# Service that attaches a survey to salesforce integration of user
def set_salesforce_survey(jobpayload, redis_instance, logger):
    try:
        # Get information from Redis
        config_json = redis_instance.hget(config["INTEGRATIONS_KEYS"]["SALESFORCE_SURVEYS"], jobpayload["publickey"])
        if config_json is None:
            return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], data={"code" : 451})
        
        # Check if credentials are valid
        config_json = json.loads(config_json.decode("utf8").replace("”", "\""))
        instance = Salesforce(username=config_json["username"], password=config_json["password"], security_token=config_json["security_token"])

        # Save information to rs-redis
        redis_payload = json.dumps({
            "survey" : jobpayload["survey"],
            "url" : jobpayload["url"],
            "username" : config_json["username"],
            "password" : config_json["password"],
            "security_token" : config_json["security_token"],
            "webhook_url" : config_json["webhook_url"]
        })

        redis_instance.hset(config["INTEGRATIONS_KEYS"]["SALESFORCE_SURVEYS"], jobpayload["publickey"], redis_payload)

        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data={"code" : 450})
    except SalesforceAuthenticationFailed as auth_error:
        logger.info(config["METHOD_ERROR_MSG"].format("get_salesforce_auth", auth_error))
        return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], error={
            "message" : "E-AUTH-SALESFORCE"
        }, data={"code" : 451})
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("set_salesforce_survey", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], data={"code" : 451})

# Update salesforce survey information / config of user
def update_salesforce_survey(jobpayload, redis_instance, logger):
    try:
        # Get information from Redis
        config_json = redis_instance.hget(config["INTEGRATIONS_KEYS"]["SALESFORCE_SURVEYS"], jobpayload["publickey"])
        if config_json is None:
            return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], data={"code" : 451})
        
        # Check if credentials are valid
        config_json = json.loads(config_json.decode("utf8").replace("”", "\""))

        payload_fields = ["survey", "url", "username", "password", "security_token", "webhook_url"]

        redis_payload_json = {}
        
        # Build json from required elements
        for field in payload_fields:
            if field in jobpayload:
                redis_payload_json[field] = jobpayload[field]
            elif field in config_json:
                redis_payload_json[field] = config_json[field]
            else:
                pass

        instance = Salesforce(username=redis_payload_json["username"], password=redis_payload_json["password"], security_token=redis_payload_json["security_token"])
        
        redis_payload = json.dumps(redis_payload_json)
        
        redis_instance.hset(config["INTEGRATIONS_KEYS"]["SALESFORCE_SURVEYS"], jobpayload["publickey"], redis_payload)

        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data={"code" : 450})

    except SalesforceAuthenticationFailed as auth_error:
        logger.info(config["METHOD_ERROR_MSG"].format("update_salesforce_survey", auth_error))
        return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], error={
            "message" : "E-AUTH-SALESFORCE"
        }, data={"code" : 451})
    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("update_salesforce_survey", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], data={"code" : 451})

# Service that gets the list of contacts for the company
def get_salesforce_contacts(jobpayload, redis_instance, logger):
    try:
        # Get information from Redis
        config_json = redis_instance.hget(config["INTEGRATIONS_KEYS"]["SALESFORCE_SURVEYS"], jobpayload["publickey"])
        if config_json is None:
            return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], data={"code" : 451})
        
        # Check if credentials are valid
        config_json = json.loads(config_json.decode("utf8").replace("”", "\""))

        instance = Salesforce(username=config_json["username"], password=config_json["password"], security_token=config_json["security_token"])

        contacts_dict = instance.query("SELECT Id, Email, Firstname, Lastname, Phone FROM Contact")
        
        if "totalSize" not in contacts_dict:
            contacts_dict = {
                "code" : 450,
                "totalSize" : 0,
                "done" : "false",
                "records" : []
            }
        
        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data=contacts_dict)

    except SalesforceAuthenticationFailed as auth_error:
        logger.info(config["METHOD_ERROR_MSG"].format("update_salesforce_survey", auth_error))
        return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], error={
            "message" : "E-AUTH-SALESFORCE"
        }, data={"code" : 451})

    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("update_salesforce_survey", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], data={"code" : 451})

# Service that disconnects salesforce account
def disconnect_salesforce_survey(jobpayload, redis_instance, logger):
    try:
        # Get information from Redis
        config_json = redis_instance.hget(config["INTEGRATIONS_KEYS"]["SALESFORCE_SURVEYS"], jobpayload["publickey"])
        if config_json is None:
            return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"])
        
        redis_instance.hdel(config["INTEGRATIONS_KEYS"]["SALESFORCE_SURVEYS"], jobpayload["publickey"])

        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data={"code" : 450})

    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("update_salesforce_survey", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], data={"code" : 451})

# Service that checks if Microsoft credentials are valid and store
def get_microsoft_auth(jobpayload, redis_instance, logger):
    try:
        app = msal.ConfidentialClientApplication(jobpayload["client_id"], authority=jobpayload["authority"], client_credential=jobpayload["secret"])
        scope = jobpayload["instance_url"] + "/.default"
        result = app.acquire_token_for_client(scopes=scope)

        if "access_token" not in result:
            return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], error={
                "message" : "E-AUTH-MICROSOFT"
            }, data={"code" : 453})
        
        # Generate webhook URL
        b64_publickey = hp.encode_string(jobpayload["publickey"])
        webhook_url = config["WEBHOOKS"]["MICROSOFT"].format(b64_publickey)

        redis_payload = json.dumps({
            "client_id" : jobpayload["client_id"],
            "secret" : jobpayload["secret"],
            "authority" : jobpayload["authority"],
            "instance_url" : jobpayload["instance_url"],
            "webhook_url" : webhook_url
        })

        # Save information to rs-redis
        redis_instance.hset(config["INTEGRATIONS_KEYS"]["MICROSOFT_SURVEYS"], jobpayload["publickey"], redis_payload)

        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data={
            "code" : 452,
            "webhook" : webhook_url
        })

    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_microsoft_auth", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], data={"code" : 453})

# Service that attaches a survey to microsoft integration of user
def set_microsoft_survey(jobpayload, redis_instance, logger):
    try:
        # Get information from Redis
        config_json = redis_instance.hget(config["INTEGRATIONS_KEYS"]["MICROSOFT_SURVEYS"], jobpayload["publickey"])
        if config_json is None:
            return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], data={"code" : 453})
        
        # Check if credentials are valid
        config_json = json.loads(config_json.decode("utf8").replace("”", "\""))

        app = msal.ConfidentialClientApplication(config_json["client_id"], authority=config_json["authority"], client_credential=config_json["secret"])
        scope = config_json["instance_url"] + "/.default"
        result = app.acquire_token_for_client(scopes=scope)

        if "access_token" not in result:
            return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], error={
                "message" : "E-AUTH-MICROSOFT"
            }, data={"code" : 453})

        # Save information to rs-redis
        redis_payload = json.dumps({
            "survey" : jobpayload["survey"],
            "url" : jobpayload["url"],
            "client_id" : config_json["client_id"],
            "secret" : config_json["secret"],
            "authority" : config_json["authority"],
            "instance_url" : config_json["instance_url"],
            "webhook_url" : config_json["webhook_url"]
        })

        redis_instance.hset(config["INTEGRATIONS_KEYS"]["MICROSOFT_SURVEYS"], jobpayload["publickey"], redis_payload)

        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data={"code" : 452})

    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("set_microsoft_survey", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], data={"code" : 453})

# Update microsoft survey information / config of user
def update_microsoft_survey(jobpayload, redis_instance, logger):
    try:
        # Get information from Redis
        config_json = redis_instance.hget(config["INTEGRATIONS_KEYS"]["MICROSOFT_SURVEYS"], jobpayload["publickey"])
        if config_json is None:
            return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], data={"code" : 453})
        
        # Check if credentials are valid
        config_json = json.loads(config_json.decode("utf8").replace("”", "\""))

        payload_fields = ["survey", "url", "client_id", "secret", "authority", "instance_url", "webhook_url"]

        redis_payload_json = {}
        
        # Build json from required elements
        for field in payload_fields:
            if field in jobpayload:
                redis_payload_json[field] = jobpayload[field]
            elif field in config_json:
                redis_payload_json[field] = config_json[field]
            else:
                pass

        app = msal.ConfidentialClientApplication(redis_payload_json["client_id"], authority=redis_payload_json["authority"], client_credential=redis_payload_json["secret"])
        scope = redis_payload_json["instance_url"] + "/.default"
        result = app.acquire_token_for_client(scopes=scope)

        if "access_token" not in result:
            return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], error={
                "message" : "E-AUTH-MICROSOFT"
            }, data={"code" : 453})
        
        redis_payload = json.dumps(redis_payload_json)
        
        redis_instance.hset(config["INTEGRATIONS_KEYS"]["MICROSOFT_SURVEYS"], jobpayload["publickey"], redis_payload)

        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data={"code" : 452})

    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("update_salesforce_survey", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], data={"code" : 453})

# Service that gets the list of microsoft contacts for the company
def get_microsoft_contacts(jobpayload, redis_instance, logger):
    try:
        # Get information from Redis
        config_json = redis_instance.hget(config["INTEGRATIONS_KEYS"]["MICROSOFT_SURVEYS"], jobpayload["publickey"])
        if config_json is None:
            return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], data={"code" : 453})
        
        # Check if credentials are valid
        config_json = json.loads(config_json.decode("utf8").replace("”", "\""))

        app = msal.ConfidentialClientApplication(config_json["client_id"], authority=config_json["authority"], client_credential=config_json["secret"])
        scope = config_json["instance_url"] + "/.default"
        result = app.acquire_token_for_client(scopes=scope)

        if "access_token" not in result:
            return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], error={
                "message" : "E-AUTH-MICROSOFT"
            }, data={"code" : 453})

        client = Client(config_json["instance_url"] + "/", token=result["access_token"])
        if not client:
            return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], error={
                "message" : "E-AUTH-MICROSOFT"
            }, data={"code" : 453})
        
        contacts = client.get_contacts(select="contactid,firstname,lastname,emailaddress1,telephone1")

        contacts_dict = {
            "code" : 452,
            "totalSize" : 0,
            "done" : "false",
            "records" : []
        }

        if "value" in contacts:
            contacts_dict = {
                "code" : 452,
                "totalSize" : len(contacts["value"]),
                "done" : "true",
                "records" : contacts["value"]
            }

        
        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data=contacts_dict)

    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("get_microsoft_contacts", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], data={"code" : 453})

# Service that disconnects microsoft account
def disconnect_microsoft_survey(jobpayload, redis_instance, logger):
    try:
        # Get information from Redis
        config_json = redis_instance.hget(config["INTEGRATIONS_KEYS"]["MICROSOFT_SURVEYS"], jobpayload["publickey"])
        if config_json is None:
            return hp.response(config['HTTP_STATUS']["HTTP_401"], config['ERROR_TITLES']["HTTP_401"], data={"code" : 453})
        
        redis_instance.hdel(config["INTEGRATIONS_KEYS"]["MICROSOFT_SURVEYS"], jobpayload["publickey"])

        return hp.response(config['HTTP_STATUS']["HTTP_200"], config['ERROR_TITLES']["HTTP_200"], data={"code" : 452})

    except Exception as e:
        logger.info(config["METHOD_ERROR_MSG"].format("delete_microsoft_survey", e))
        return hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], data={"code" : 453})

def check_survey_assigned(viewid, jobpayload, logger):
    try:
        state = False
        codes = []
        integration_codes = {
            "SALESFORCE" : 405,
            "MICROSOFT" : 406
        }
        for integration in config["INTEGRATIONS_IMPLEMENTED"]:
            config_json = rs_redis.hget(integration + "_SURVEYS", jobpayload["alias"])
            if config_json is not None:
                config_json = json.loads(config_json.decode("utf8").replace("”", "\""))
                if "survey" in config_json and config_json["survey"] == viewid:
                    int_string = integration_codes[integration]
                    state = True
                    codes.append(int_string)
        return state, codes
    except Exception as e:
        logger.info(str(e))
        return False, ""