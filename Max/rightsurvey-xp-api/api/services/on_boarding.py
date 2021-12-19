import sys

sys.path.append("/usr/src/app/api")
from redis import StrictRedis
from logging import Logger
from core.settings import config
import json


class OnBoardingService(object):

    def __init__(self, redis_instance: StrictRedis):
        self.redis_instance = redis_instance

    # this method allow to check if onboarding was already done
    def check(self, user_data: dict, logger: Logger) -> bool:
        logger.info("user data get is: %s" % user_data)
        publickey = user_data["data"]["alias"]
        key = config["ONBOARDING_REDIS_TAG"] + publickey
        logger.info("key: %s" % key)
        if self.redis_instance.exists(key):
            return True
        return False

    # this method allow to update the user onboarding state
    def update(self, user_data: dict, logger: Logger):
        logger.info("user data get is: %s" % user_data)
        publickey = user_data["data"]["alias"]
        key = config["ONBOARDING_REDIS_TAG"] + publickey
        self.redis_instance.set(key, json.dumps(user_data))
