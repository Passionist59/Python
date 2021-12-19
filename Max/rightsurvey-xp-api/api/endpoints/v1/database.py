import sys

sys.path.append("/usr/src/app/api")
import falcon
from utils import helpers as hp
from core.settings import config
from core.dbbatch import generate_database

logger = hp.get_logger(config["LOGGER"]['DATABASE_ENDPOINT'], config["LOG_FILES"]['DATABASE_ENDPOINT_LOG'])


class Databases(object):
    auth = {
        'auth_disabled': True
    }

    def on_get(self, req, resp):
        try:
            database = req.get_param('database', None)
            company = req.get_param('company', None)
            formula = req.get_param('formula', 'NORMAL')
            alias = req.get_param('alias', None)
            logger.info(
                "create a new database for company -> " + company + " with dbname -> " + database + ", formula-> " + formula + " and alias-> " + alias)

            if not database or not company or not alias or not formula:
                resp.status = falcon.HTTP_BAD_REQUEST
                resp.body = hp.response(config["HTTP_STATUS"]["HTTP_400"], config["ERROR_TITLES"]["HTTP_400"],
                                        error={"code": config["ERROR_CODE"]["MISSING_DATABASE_PARAMETERS"],
                                               "params": ["database", "company", "formula", "alias"]})
                return

            result = generate_database(database, company, logger)
            logger.info('Data received after setup => ' + str(result))
            resp.status = falcon.HTTP_OK
            resp.body = hp.response(config["HTTP_STATUS"]["HTTP_200"], config["ERROR_TITLES"]["HTTP_200"], data=result)
            return

        except Exception as e:
            logger.info("There is an error on post database: %s" % e)
            resp.status = falcon.HTTP_200
            resp.body = hp.response(config["HTTP_STATUS"]["HTTP_500"], config["ERROR_TITLES"]["HTTP_500"])
            return
