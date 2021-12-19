# -*- coding: utf-8 -*-
"""
This file define all services for integration RightCare application
"""

import sys

sys.path.append("/usr/src/app/api")
from core.request_connector import RequestConnector
from core.settings import config
from logging import Logger


class RightCareServices(object):

    def __init__(self, request: RequestConnector, logger: Logger):
        self.request = request
        self.logger = logger

    def create_configuration(self, data: dict, header: dict) -> tuple:
        self.logger.info("We are in method named : create_configuration")
        url = config["RIGHTCARE_BASE_URL"] + config["RIGHTCARE_SERVICE"]["CREATE_CONFIG"]
        self.logger.info(config["INFO_MSG_URL"].format(url))
        self.logger.info(f'header = {header}')
        response = self.request.post(url, data=data, headers=header, timeout=10)
        self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
        return response.get(config["REQUEST_RESPONSE_ATTR_DATA"])["status"] == config[
            "REQUEST_RESPONSE_CODE_200"], response.get(config["REQUEST_RESPONSE_ATTR_DATA"])

    def update_configuration(self, viewid: str, data: dict, header) -> tuple:
        self.logger.info("We are in method named : update_configuration")
        url = config["RIGHTCARE_BASE_URL"] + config["RIGHTCARE_SERVICE"]["UPDATE_CONFIG"] + '/' + viewid
        self.logger.info(config["INFO_MSG_URL"].format(url))
        response = self.request.put(url, data=data, headers=header, timeout=10)
        self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
        return response.get(config["REQUEST_RESPONSE_ATTR_DATA"])["status"] == config[
            "REQUEST_RESPONSE_CODE_200"], response.get(config["REQUEST_RESPONSE_ATTR_DATA"])

    def delete_configuration(self, viewid: str, header: dict) -> bool:
        self.logger.info("We are in method named : delete_configuration")
        url = config["RIGHTCARE_BASE_URL"] + config["RIGHTCARE_SERVICE"]["DELETE_CONFIG"] + '/' + viewid
        self.logger.info(config["INFO_MSG_URL"].format(url))
        response = self.request.delete(url, headers=header, timeout=10)
        self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
        return response.get(config["REQUEST_RESPONSE_ATTR_DATA"])["status"] == config["REQUEST_RESPONSE_CODE_200"]

    def get_list_configuration(self, header: dict) -> tuple:
        self.logger.info("We are in method named : get_list_configuration")
        url = f'{config["RIGHTCARE_BASE_URL"]}{config["RIGHTCARE_SERVICE"]["LIST_CONFIG"]}'
        self.logger.info(config["INFO_MSG_URL"].format(url))
        response = self.request.get(url, headers=header, timeout=10)
        self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
        return response.get(config["REQUEST_RESPONSE_ATTR_DATA"])["status"] == config[
            "REQUEST_RESPONSE_CODE_200"], response.get(config["REQUEST_RESPONSE_ATTR_DATA"])

    def create_ticket(self, data: dict) -> tuple:
        self.logger.info("We are in method named : create_ticket")
        url = f'{config["RIGHTCARE_BASE_URL"]}{config["RIGHTCARE_SERVICE"]["CREATE_TICKET"]}'
        self.logger.info(config["INFO_MSG_URL"].format(url))
        response = self.request.post(url, data=data, timeout=10)
        self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
        return response.get(config["REQUEST_RESPONSE_ATTR_DATA"])["status"] == config[
            "REQUEST_RESPONSE_CODE_200"], response.get(config["REQUEST_RESPONSE_ATTR_DATA"])

    def check_survey_is_configured(self, viewid: str, header: dict) -> bool:
        self.logger.info("We are in method named : check_survey_is_configured")
        url: str = f'{config["RIGHTCARE_BASE_URL"]}{config["RIGHTCARE_SERVICE"]["CHECK_STATE"]}?viewid={viewid}'
        self.logger.info(config["INFO_MSG_URL"].format(url))
        response = self.request.get(url, headers=header, timeout=10)
        self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
        response_data = response.get(config["REQUEST_RESPONSE_ATTR_DATA"])
        self.logger.info(f'response data = {response_data}')
        if not response_data:
            return False
        if response_data["status"] != 200:
            return False
        return response_data.get(config["REQUEST_RESPONSE_ATTR_DATA"])["state"]

    def get_customer_agent_list(self, header: dict) -> tuple:
        self.logger.info("We are in method named : get_customer_agent_list")
        url = f'{config["RIGHTCARE_BASE_URL"]}{config["RIGHTCARE_SERVICE"]["LIST_AGENT"]}'
        self.logger.info(config["INFO_MSG_URL"].format(url))
        response = self.request.get(url, headers=header, timeout=10)
        self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
        return response.get(config["REQUEST_RESPONSE_ATTR_DATA"])["status"] == config["REQUEST_RESPONSE_CODE_200"], \
               response.get(config["REQUEST_RESPONSE_ATTR_DATA"])[config["REQUEST_RESPONSE_ATTR_DATA"]]
