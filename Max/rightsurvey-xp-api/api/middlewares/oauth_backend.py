# -*- coding: utf-8 -*-
"""
this module is an extension of falcon_auth.backends backends
"""
import sys

sys.path.append("/usr/src/app/api")
import falcon
from falcon_auth.backends import AuthBackend
from third_party.xp_services import AccountCustomerService
from core.settings import config
from logging import Logger
import json
from redis import StrictRedis


class XpOauthBackend(AuthBackend):
    """
    This class ensures that the publickey, apisid and the sessionid provided by the client are valid
    If the inputs are not provided a falcon.UNAUTHORIZED exception is raised
    """

    def __init__(self, user_loader, service: AccountCustomerService, logger: Logger, redis_instance: StrictRedis,
                 redis_checker, auth_header_prefix: str = None):
        self.user_loader = user_loader
        self.auth_header_prefix = auth_header_prefix
        self.service = service
        self.logger = logger
        self.redis_instance = redis_instance
        self.redis_checker = redis_checker

    def _extract_credentials(self, req: falcon.Request) -> dict:
        """
        This method retrieves connection information from the header
        :param req: request object
        :return:
        """
        self.logger.info("_extract_credentials method")
        publickey = req.get_header(config["ADMIN_SERVICE"]["PUBLICKEY"])
        self.logger.info("publickey: %s" % publickey)
        apisid = req.get_header(config["ADMIN_SERVICE"]["APISID"])
        self.logger.info("apisid: %s" % apisid)
        sessionid = req.get_header(config["ADMIN_SERVICE"]["SESSIONID"])
        self.logger.info("sessionid: %s" % sessionid)
        if publickey is None or apisid is None or sessionid is None:
            raise falcon.HTTPUnauthorized('Authorization publickey, sessionid and apisid required', '', '', href='')

        return {config["ADMIN_SERVICE"]["PUBLICKEY"]: publickey, config["ADMIN_SERVICE"]["APISID"]: apisid,
                config["ADMIN_SERVICE"]["SESSIONID"]: sessionid}

    def authenticate(self, req: falcon.Request, resp: falcon.Response, resource):
        """
        retrieves the information in the header, verifies that an active session exists for the user
        and returns the information from the client, else raise an `falcon.HTTPUnauthorized exception`
        :param req:
        :param resp:
        :param resource:
        :return:
        """
        self.logger.info("authenticate method")
        credentials = self._extract_credentials(req)
        self.logger.info("credentials: %s" % credentials)
        if 'doc' not in req.context:
            req.context['doc'] = credentials
        if not req.context['doc'].get(config["ADMIN_SERVICE"]["PUBLICKEY"]): req.context['doc'][
            config["ADMIN_SERVICE"]["PUBLICKEY"]] = credentials[config["ADMIN_SERVICE"]["PUBLICKEY"]]
        if not req.context['doc'].get(config["ADMIN_SERVICE"]["APISID"]): req.context['doc'][
            config["ADMIN_SERVICE"]["APISID"]] = credentials[config["ADMIN_SERVICE"]["APISID"]]
        if not req.context['doc'].get(config["ADMIN_SERVICE"]["SESSIONID"]): req.context['doc'][
            config["ADMIN_SERVICE"]["SESSIONID"]] = credentials[config["ADMIN_SERVICE"]["SESSIONID"]]
        check_auth, data = self.service.session_is_valid(**credentials)
        self.logger.info("check_auth: %s" % check_auth)
        self.logger.info("data: %s" % data)
        if check_auth:
            req.context['doc']['user'] = data
            self.logger.info("alias: %s" % data["data"]["alias"])
            publickey = data["data"]["alias"]
            session_user = data["data"]['user']
            key = config["FOUNDATION_REDIS_TAG"] + publickey
            result = self.redis_checker(key, self.redis_instance)
            if not result:
                result = self.service.get_customer_database(publickey)
                if not result:
                    raise falcon.HTTPUnauthorized('Failed to get customer database informations', '', '', href='')
                self.redis_instance.set(key, json.dumps(result))
            req.context['doc']['database'] = result["data"]
            return True
        else:
            raise falcon.HTTPUnauthorized('Authorization publickey, sessionid and apisid required', '', '', href='')

    def get_auth_token(self, payload: dict) -> dict:
        """
        it provides the structure of the necessary headers with the values ​​to pass the authentication
        :param user_payload:
        :return:
        """
        return {
            config["ADMIN_SERVICE"]["PUBLICKEY"]: payload.get(config["ADMIN_SERVICE"]["PUBLICKEY"]),
            config["ADMIN_SERVICE"]["APISID"]: payload.get(config["ADMIN_SERVICE"]["APISID"]),
            config["ADMIN_SERVICE"]["SESSIONID"]: payload.get(config["ADMIN_SERVICE"]["SESSIONID"]),
        }
