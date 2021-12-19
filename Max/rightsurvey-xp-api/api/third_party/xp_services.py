# -*- coding: utf-8 -*-
"""
This file define all services for integration RightComXp Core application
"""

import sys

sys.path.append("/usr/src/app/api")
from core.request_connector import RequestConnector
from core.settings import config
from logging import Logger


class AccountCustomerService(object):

    def __init__(self, request: RequestConnector, logger: Logger):
        self.request = request
        self.logger = logger

    # method that allow you to validate a current user session
    def session_is_valid(self, publickey: str, apisid: str, sessionid: str):
        self.logger.info("We are in method named: session_is_valid")
        url = config["ADMIN_BASE_URL"] + config["ADMIN_SERVICE"]["VALID_SESSION"]
        self.logger.info(config["INFO_MSG_URL"].format(url))
        queries = {
            config["ADMIN_SERVICE"]["PUBLICKEY"]: publickey,
            config["ADMIN_SERVICE"]["APISID"]: apisid,
            config["ADMIN_SERVICE"]["SESSIONID"]: sessionid,
            config["ADMIN_SERVICE"]["APPID"]: config["APPID"]
        }
        self.logger.info(config["INFO_MSG_QUERIES"].format(queries))
        response = self.request.get(url, query=queries, timeout=10)
        self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
        return response.get(config["REQUEST_RESPONSE_ATTR_DATA"])["status"] == config[
            "REQUEST_RESPONSE_CODE_200"], response.get(config["REQUEST_RESPONSE_ATTR_DATA"])

    # method that allow the frontend to know if user have a valid session or not
    def session_decoder(self, alias: str, app_id: str, sid: str):
        self.logger.info("We are in method named: session_decoder")
        url = config["DECODER_BASE_URL"] + config["SESSION_SERVICE"]["CHECK"]
        self.logger.info(config["INFO_MSG_URL"].format(url))
        queries = {
            config["SESSION_SERVICE"]["ALIAS"]: alias,
            config["SESSION_SERVICE"]["APPID"]: app_id,
            config["SESSION_SERVICE"]["SID"]: sid
        }
        self.logger.info(config["INFO_MSG_QUERIES"].format(queries))
        response = self.request.get(url, query=queries, timeout=10)
        self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
        if response.get(config["REQUEST_RESPONSE_ATTR_CODE"]) == config["REQUEST_RESPONSE_CODE_200"]:
            return True, response.get(config["REQUEST_RESPONSE_ATTR_DATA"])
        return False, {}

    # method that allow to get current customer database informations
    def get_customer_database(self, publickey: str):
        self.logger.info("We are in method named: get_customer_database")
        url = config["FOUNDATION_BASE_URL"] + config["FOUNDATION_SERVICE"]["CUSTOMER_DATABASE"]
        self.logger.info(config["INFO_MSG_URL"].format(url))
        queries = {
            config["FOUNDATION_SERVICE"]["PUBLICKEY"]: publickey,
            config["FOUNDATION_SERVICE"]["PRODUCT"]: config["FOUNDATION_PRODUCT_CODE"]
        }
        self.logger.info(config["INFO_MSG_QUERIES"].format(queries))
        response = self.request.get(url, query=queries, timeout=10)
        self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
        if response.get(config["REQUEST_RESPONSE_ATTR_CODE"]) == config["REQUEST_RESPONSE_CODE_200"]:
            return response.get(config["REQUEST_RESPONSE_ATTR_DATA"])
        return None

    def get_account_users(self, publickey: str, appid: str):
        url = config["ADMIN_BASE_URL"] + config["ADMIN_SERVICE"]["APP_USERS"]
        queries = {
            "alias": publickey,
            config["ADMIN_SERVICE"]["APPID"]: appid
        }
        response = self.request.get(url, query=queries, timeout=10)
        self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
        return response.get(config["REQUEST_RESPONSE_ATTR_DATA"])[config["REQUEST_RESPONSE_ATTR_DATA"]]

    def get_client_app(self, publickey: str, apisid: str, sessionid: str) -> tuple:
        self.logger.info("We are in method named: get_client_app")
        url = config["ADMIN_BASE_URL"] + config["ADMIN_SERVICE"]["CLIENT_APP_LIST"]
        self.logger.info(config["INFO_MSG_URL"].format(url))
        header: dict = {
            'apisid': apisid,
            'publickey': publickey,
            'sessionid': sessionid
        }
        self.logger.info(f'header = {header}')
        response = self.request.get(url, headers=header, timeout=10)
        self.logger.info(f'get_client_app => response got from a server : {response}')
        self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
        return response.get(config["REQUEST_RESPONSE_ATTR_DATA"])["status"] == config[
            "REQUEST_RESPONSE_CODE_200"], response.get(config["REQUEST_RESPONSE_ATTR_DATA"])

    def get_connected_user_license(self, apisid: str, alias: str, product_code: str) -> dict:
        url = config["PAYMENT_BASE_URL"] + config["PAYMENT_SERVICE_PATH"]["LICENSE_STATUS"]
        queries = {
            'apisid': apisid,
            'alias': alias,
            'product_code': product_code
        }
        response = self.request.get(url, query=queries, timeout=10)
        self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
        return response.get(config["REQUEST_RESPONSE_ATTR_DATA"])[config["REQUEST_RESPONSE_ATTR_DATA"]]

    def get_app_users(self, apisid: str, sessionid: str, publickey: str) -> list:
        """Allow to retrieve a user list assign to rightsurvey app
        :param apisid: first user session parameter
        :type apisid: str
        :param sessionid: second user session parameter
        :type sessionid: str
        :param publickey: third user session parameter
        :type publickey: str
        :return: list of users assign to rightsurvey
        :rtype: list
        """
        pass
