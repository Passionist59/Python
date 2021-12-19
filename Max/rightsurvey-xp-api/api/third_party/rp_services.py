import sys

sys.path.append("/usr/src/app/api")
from core.request_connector import RequestConnector
from core.settings import config
from logging import Logger


class RightPaymentServices:
	def __init__(self, request: RequestConnector, logger: Logger):
		self.request = request
		self.logger = logger

	def get_account_status(self, publickey: str) -> tuple:
		self.logger.info("We are in method named : get_account_status")
		self.logger.info(f"publickey => {publickey}")
		url = f'{config["RIGHTPAYMENT_BASE_URL"]}{config["RIGHTPAYMENT_SERVICE"]["ACCOUNT_STATUS"]}'
		self.logger.info(config["INFO_MSG_URL"].format(url))
		query: dict = {'publickey': publickey}
		response = self.request.get(url, query=query, timeout=10)
		self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
		response_body: dict = response.get(config["REQUEST_RESPONSE_ATTR_DATA"])
		status: bool = response_body["status"] == config["REQUEST_RESPONSE_CODE_200"]
		result: dict = response_body[config["REQUEST_RESPONSE_ATTR_DATA"]]
		return status, result

	def update_response_count(self, viewid: str, publickey: str) -> tuple:
		self.logger.info("We are in method named : update_response_count")
		url = f'{config["RIGHTPAYMENT_BASE_URL"]}{config["RIGHTPAYMENT_SERVICE"]["RESPONSE_COUNT"]}'
		url += f'?viewid={viewid}&publickey={publickey}'
		self.logger.info(config["INFO_MSG_URL"].format(url))
		response = self.request.put(url, data={}, timeout=10)
		self.logger.info(config["INFO_MSG_RESPONSE"].format(response))
		response_body: dict = response.get(config["REQUEST_RESPONSE_ATTR_DATA"])
		status: bool = response_body["status"] == config["REQUEST_RESPONSE_CODE_200"]
		result: dict = response_body[config["REQUEST_RESPONSE_ATTR_DATA"]]
		return status, result
