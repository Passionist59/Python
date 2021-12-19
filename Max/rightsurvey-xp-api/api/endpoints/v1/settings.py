import sys

sys.path.append("/usr/src/app/api")
import falcon
from utils import helpers as hp
from core.settings import config
from services.settings import setup_logo, setup_welcome_msg, setup_thank_you_msg, get_settings
from utils import models as md

logger = hp.get_logger(config['LOGGER']['SETTINGS_ENDPOINT'], config['LOG_FILES']['SETTINGS_ENDPOINT_LOG'])


class Settings(object):

	def on_get(self, req, resp) -> None:
		try:
			logger.info(f"Customer database informations: {req.context['doc']['database']}")
			payload = {
				"collection": "settings",
				"database": req.context['doc']['database']
			}
			status_code, result = get_settings(payload, logger)
			data = dict(settings=result) if status_code == 200 else {}
			error = dict(message=result) if status_code != 200 else {}
			resp.status = falcon.HTTP_OK
			resp.body = hp.response(config['HTTP_STATUS'][f"HTTP_{status_code}"],
									config['ERROR_TITLES'][f"HTTP_{status_code}"],
									data=data, error=error)
			return

		except Exception as e:
			logger.info(f"The following error was occured : {e}")
			resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
			resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], error=f"{e}")
			return

	def on_post_logo(self, req, resp) -> None:
		try:
			if not hp.validate_params_by_model(req.context['doc'], md.logo):
				resp.status = falcon.HTTP_BAD_REQUEST
				error: dict = {
					"code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
					"params": md.logo,
				}
				resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
										error=error)
				return

			# Retrieve fields values from request instance
			payload = {
				"link": req.context['doc']['link'],
				"display_size_option": req.context['doc']['display_size_option'],
				"position": req.context['doc']['position'],
				"database": req.context['doc']['database'],
				"collection": "settings"
			}
			status_code, result = setup_logo(payload, logger)
			data = dict(settigs=result) if status_code == 200 else {}
			error = dict(message=result) if status_code != 200 else {}
			resp.status = falcon.HTTP_OK
			resp.body = hp.response(config['HTTP_STATUS'][f"HTTP_{status_code}"],
									config['ERROR_TITLES'][f"HTTP_{status_code}"],
									data=data, error=error)
			return

		except Exception as e:
			logger.info(f"The following error was occured : {e}")
			resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
			resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], error=f"{e}")
			return

	def on_post_welcome(self, req, resp) -> None:
		try:
			if not hp.validate_params_by_model(req.context['doc'], md.welcome):
				resp.status = falcon.HTTP_BAD_REQUEST
				error: dict = {
					"code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
					"params": md.welcome,
				}
				resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
										error=error)
				return

			# Retrieve fields values from request instance
			payload = {
				"option": req.context['doc']['option'],
				"heading_text": req.context['doc']['heading_text'],
				"message": req.context['doc']['message'],
				"database": req.context['doc']['database'],
				"collection": "settings"
			}
			status_code, result = setup_welcome_msg(payload, logger)
			data = dict(settigs=result) if status_code == 200 else {}
			error = dict(message=result) if status_code != 200 else {}
			resp.status = falcon.HTTP_OK
			resp.body = hp.response(config['HTTP_STATUS'][f"HTTP_{status_code}"],
									config['ERROR_TITLES'][f"HTTP_{status_code}"],
									data=data, error=error)
			return

		except Exception as e:
			logger.info(f"The following error was occured : {e}")
			resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
			resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], error=f"{e}")
			return

	def on_post_thank_you(self, req, resp) -> None:
		try:
			if not hp.validate_params_by_model(req.context['doc'], md.thank_you):
				resp.status = falcon.HTTP_BAD_REQUEST
				error: dict = {
					"code": config['ERROR_CODE']["MISSING_REQUIRE_PARAMETER"],
					"params": md.thank_you,
				}
				resp.body = hp.response(config['HTTP_STATUS']["HTTP_400"], config['ERROR_TITLES']["HTTP_400"],
										error=error)
				return

			# Retrieve fields values from request instance
			payload = {
				"option": req.context['doc']['option'],
				"heading_text": req.context['doc']['heading_text'],
				"message": req.context['doc']['message'],
				"image": req.context['doc']['image'],
				"database": req.context['doc']['database'],
				"collection": "settings"
			}
			status_code, result = setup_thank_you_msg(payload, logger)
			data = dict(settigs=result) if status_code == 200 else {}
			error = dict(message=result) if status_code != 200 else {}
			resp.status = falcon.HTTP_OK
			resp.body = hp.response(config['HTTP_STATUS'][f"HTTP_{status_code}"],
									config['ERROR_TITLES'][f"HTTP_{status_code}"],
									data=data, error=error)
			return

		except Exception as e:
			logger.info(f"The following error was occured : {e}")
			resp.status = falcon.HTTP_INTERNAL_SERVER_ERROR
			resp.body = hp.response(config['HTTP_STATUS']["HTTP_500"], config['ERROR_TITLES']["HTTP_500"], error=f"{e}")
			return
