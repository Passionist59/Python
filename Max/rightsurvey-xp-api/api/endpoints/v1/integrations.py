import sys

sys.path.append("/usr/src/app/api")
import falcon
from utils import helpers as hp
from core.settings import config
from services import integrations as sv
from utils import models as md

logger = hp.get_logger(config['LOGGER']['INTEGRATIONS_ENDPOINT'], config['LOG_FILES']['INTEGRATIONS_ENDPOINT_LOG'])

class Integrations(object):
    main_endpoint = "integrations"

    def __init__(self, redis_instance):
        self.redis_instance = redis_instance
    
    # Get list of integrations implemented with status
    def on_get(self, req, resp):
        try:
            logger.info("Customer database informations: %s" % req.context['doc']['database'])
            payload = {
                "publickey" : req.context['doc']['user']["data"]["alias"],
                "database" : req.context['doc']['database']
            }
            result = sv.get_integrations(payload, self.redis_instance, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception as e:
            logger.info(e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    # Get list of contacts from Salesforce CRM
    def on_get_salesforce(self, req, resp):
        try:
            logger.info("Customer database informations: %s" % req.context['doc']['database'])
            payload = {
                "publickey" : req.context['doc']['user']["data"]["alias"]
            }
            result = sv.get_salesforce_contacts(payload, self.redis_instance, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception as e:
            logger.info(e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    # Endpoint to check provided credentials
    def on_post_salesforce(self, req, resp):
        try:
            logger.info("Customer database informations: %s" % req.context['doc']['database'])
            current_endpoint = self.main_endpoint + "_salesforce_post"

            if not hp.validate_params(current_endpoint, req.context['doc']):
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": config['REQUIRED_FIELDS_MAP'][current_endpoint]
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"], error=error)
                return

            payload = {
                "username": req.context["doc"].get('username'),
                "password": req.context["doc"].get('password'),
                "security_token": req.context["doc"].get('security_token'),
                "publickey": req.context['doc']['user']["data"]["alias"]
            }

            result = sv.get_salesforce_auth(payload, self.redis_instance, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception as e:
            logger.info(e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return
    
    # Endpoint to assign survey to a company
    def on_put_salesforce(self, req, resp):
        try:
            logger.info("Customer database informations: %s" % req.context['doc']['database'])
            current_endpoint = self.main_endpoint + "_salesforce_put"
            
            if not hp.validate_params(current_endpoint, req.context['doc']):
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": config['REQUIRED_FIELDS_MAP'][current_endpoint]
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"], error=error)
                return

            payload = {
                "survey" : req.context['doc'].get('survey'),
                "url" : req.context['doc'].get('url'),
                "publickey": req.context['doc']['user']["data"]["alias"]
            }

            result = sv.set_salesforce_survey(payload, self.redis_instance, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception as e:
            logger.info(e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return
    
    # Endpoint to update survey information / credentials
    def on_patch_salesforce(self, req, resp):
        try:
            logger.info("Customer database informations: %s" % req.context['doc']['database'])
            current_endpoint = self.main_endpoint + "_salesforce_patch"
            
            payload = req.context['doc'] 
            payload["publickey"] = req.context['doc']['user']["data"]["alias"]

            result = sv.update_salesforce_survey(payload, self.redis_instance, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception as e:
            logger.info(e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return
    
    # Endpoint to disconnect salesforce integration
    def on_delete_salesforce(self, req, resp):
        try:
            logger.info("Customer database informations: %s" % req.context['doc']['database'])
            current_endpoint = self.main_endpoint + "_salesforce_delete"
            
            payload = {
                "publickey" : req.context['doc']['user']["data"]["alias"]
            }

            result = sv.disconnect_salesforce_survey(payload, self.redis_instance, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception as e:
            logger.info(e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    # Get list of contacts from Salesforce CRM
    def on_get_microsoft(self, req, resp):
        try:
            logger.info("Customer database informations: %s" % req.context['doc']['database'])
            payload = {
                "publickey" : req.context['doc']['user']["data"]["alias"]
            }
            result = sv.get_microsoft_contacts(payload, self.redis_instance, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception as e:
            logger.info(e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return

    # Endpoint to check provided credentials
    def on_post_microsoft(self, req, resp):
        try:
            logger.info("Customer database informations: %s" % req.context['doc']['database'])
            current_endpoint = self.main_endpoint + "_microsoft_post"

            if not hp.validate_params(current_endpoint, req.context['doc']):
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": config['REQUIRED_FIELDS_MAP'][current_endpoint]
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"], error=error)
                return

            payload = {
                "client_id": req.context["doc"].get('client_id'),
                "secret": req.context["doc"].get('secret'),
                "authority": req.context["doc"].get('authority'),
                "instance_url": req.context["doc"].get('instance_url'),
                "publickey": req.context['doc']['user']["data"]["alias"]
            }

            result = sv.get_microsoft_auth(payload, self.redis_instance, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception as e:
            logger.info(e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return
    
    # Endpoint to assign survey to a company
    def on_put_microsoft(self, req, resp):
        try:
            logger.info("Customer database informations: %s" % req.context['doc']['database'])
            current_endpoint = self.main_endpoint + "_microsoft_put"
            
            if not hp.validate_params(current_endpoint, req.context['doc']):
                resp.status = falcon.HTTP_BAD_REQUEST
                error = {
                    "code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
                    "params": config['REQUIRED_FIELDS_MAP'][current_endpoint]
                }
                resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"], error=error)
                return

            payload = {
                "survey" : req.context['doc'].get('survey'),
                "url" : req.context['doc'].get('url'),
                "publickey": req.context['doc']['user']["data"]["alias"]
            }

            result = sv.set_microsoft_survey(payload, self.redis_instance, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception as e:
            logger.info(e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return
    
    # Endpoint to update survey information / credentials
    def on_patch_microsoft(self, req, resp):
        try:
            logger.info("Customer database informations: %s" % req.context['doc']['database'])
            current_endpoint = self.main_endpoint + "_microsoft_patch"
            
            payload = req.context['doc'] 
            payload["publickey"] = req.context['doc']['user']["data"]["alias"]

            result = sv.update_microsoft_survey(payload, self.redis_instance, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception as e:
            logger.info(e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return
    
    # Endpoint to disconnect microsoft integration
    def on_delete_microsoft(self, req, resp):
        try:
            logger.info("Customer database informations: %s" % req.context['doc']['database'])
            current_endpoint = self.main_endpoint + "_microsoft_delete"
            
            payload = {
                "publickey" : req.context['doc']['user']["data"]["alias"]
            }

            result = sv.disconnect_microsoft_survey(payload, self.redis_instance, logger)
            resp.status = falcon.HTTP_OK
            resp.body = result
            return
        except Exception as e:
            logger.info(e)
            resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
            resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"])
            return