# -*- coding: utf-8 -*-
import sys

sys.path.append("/usr/src/app/api")
from logging import Logger
from core.dbutils import add, edit_one, get_list, get_one, check_collection_exists, add_collection


def setup_logo(payload: dict, logger: Logger) -> tuple:
	try:
		logger.info(f"payload ==> {payload}")
		collection = payload.get("collection")
		database = payload.get("database")
		link = payload.get("link")
		display_size_option = payload.get("display_size_option")
		position = payload.get("position")
		properties = {"link": link, "display_size_option": display_size_option, "position": position}

		status, completed = check_collection_exists(database["dbname"], database["dbuser"], database["dbpassword"],
													collection)
		logger.info(f"status ==> {status} | completed ==> {completed}")
		if not status and completed:
			res = add_collection(database["dbname"], database["dbuser"], database["dbpassword"], collection)
			logger.info(f"result ==> {res[0]} and completed {res[1]}")

		setting, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
								  {'name': 'logo'})
		logger.info(f"Setting ==> {setting} | completed ==> {status}")

		error, state = edit_one(database=database["dbname"], username=database["dbuser"], pwd=database["dbpassword"],
								collection=collection, criteria={'name': 'logo'}, param={"properties": properties},
								listback=False) if setting else add(database["dbname"], database["dbuser"],
																	database["dbpassword"], collection,
																	{"name": "logo", "properties": properties},
																	listback=False)
		logger.info(f"error ==> {error} and status ==> {state}")
		if not state:
			return 500, f"Failed with error message : {e}"
		return 200, "Successfully make a setup"

	except Exception as e:
		logger.info(f"The following error was occured : {e}")
		return 500, f'This {e} was occured'


def setup_welcome_msg(payload: dict, logger: Logger) -> tuple:
	try:
		collection = payload.get("collection")
		database = payload.get("database")
		option = payload.get("option")
		heading_text = payload.get("heading_text")
		message = payload.get("message")
		properties = {"option": option, "heading_text": heading_text, "message": message}

		status, completed = check_collection_exists(database["dbname"], database["dbuser"], database["dbpassword"],
													collection)
		logger.info(f"status ==> {status} | completed ==> {completed}")
		if not status and completed:
			res = add_collection(database["dbname"], database["dbuser"], database["dbpassword"], collection)
			logger.info(f"result ==> {res[0]} and completed {res[1]}")

		setting, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
								  {'name': 'welcome'})
		logger.info(f"setting ==> {setting} | completed ==> {status}")
		err, state = edit_one(database=database["dbname"], username=database["dbuser"], pwd=database["dbpassword"],
							  collection=collection, criteria={'name': 'welcome'},
							  param={"properties": properties}) if setting else add(database["dbname"],
																					database["dbuser"],
																					database["dbpassword"], collection,
																					{"name": "welcome",
																					 "properties": properties},
																					listback=False)
		logger.info(f"error ==> {err} and status ==> {state}")
		if not state:
			return 500, f"Failed with error message : {e}"
		return 200, "Successfully make a setup"

	except Exception as e:
		logger.info(f"The following error was occured : {e}")
		return 500, f'This {e} was occured'


def setup_thank_you_msg(payload: dict, logger: Logger) -> tuple:
	try:
		collection = payload.get("collection")
		database = payload.get("database")
		option = payload.get("option")
		heading_text = payload.get("heading_text")
		message = payload.get("message")
		image = payload.get("image")
		properties = {"option": option, "heading_text": heading_text, "message": message, "image": image}

		status, completed = check_collection_exists(database["dbname"], database["dbuser"], database["dbpassword"],
													collection)
		if not status and completed:
			res = add_collection(database["dbname"], database["dbuser"], database["dbpassword"], collection)
			logger.info(f"result ==> {res[0]} and completed {res[1]}")

		setting, status = get_one(database['dbname'], database['dbuser'], database['dbpassword'], collection,
								  {'name': 'thank you'})
		logger.info(f"setting ==> {setting} | completed ==> {status}")
		err, state = edit_one(database=database["dbname"], username=database["dbuser"], pwd=database["dbpassword"],
							  collection=collection, criteria={'name': 'thank you'},
							  param={"properties": properties}) if setting else add(database["dbname"],
																					database["dbuser"],
																					database["dbpassword"], collection,
																					{"name": "thank you",
																					 "properties": properties},
																					listback=False)
		logger.info(f"error ==> {err} and status ==> {state}")
		if not state:
			return 500, f"Failed with error message : {e}"
		return 200, "Successfully make a setup"

	except Exception as e:
		logger.info(f"The following error was occured : {e}")
		return 500, f'This {e} was occured'


def get_settings(payload: dict, logger: Logger) -> tuple:
	try:
		collection = payload.get("collection")
		database = payload.get("database")
		status, completed = check_collection_exists(database["dbname"], database["dbuser"], database["dbpassword"],
													collection)
		if not status and completed:
			add_collection(database["dbname"], database["dbuser"], database["dbpassword"], collection)
		query: dict = {
			'database': database['dbname'], 'username': database["dbuser"],
		   	'pwd': database["dbpassword"], 'collection': collection, 'paginator': None,
		   	'projection': {'_id': False, 'id': False, 'viewid': False, 'created_at': False, 'updated_at': False}
		}
		settings, _ = get_list(**query)
		logger.info(f"result => {settings}")
		if not settings and len(settings) == 0:
			thank_you_setting = {
				"name": "thank you",
				"properties": {'option': 'default', 'image': '', 'message': '', 'heading_text': ''}
			}
			add(database["dbname"], database["dbuser"], database["dbpassword"], collection, {"name": "thank you", "properties": thank_you_setting}, listback=False)
			welcome_setting = {"option": 'default', "heading_text": '', "message": ''}
			add(database["dbname"], database["dbuser"], database["dbpassword"], collection, {"name": "welcome", "properties": welcome_setting}, listback=False)
			logo_setting = {"link": '', "display_size_option": '', "position": ''}
			add(database["dbname"], database["dbuser"], database["dbpassword"], collection, {"name": "logo", "properties": logo_setting}, listback=False)
			settings, _ = get_list(**query)

		return 200, settings

	except Exception as e:
		logger.info(f"The following error was occured : {e}")
		return 500, f'This {e} was occured'
