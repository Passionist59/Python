import sys

sys.path.append("/usr/src/app/api")
import logging
from logging import Logger
import json
import redis
import random
import base64
import qrcode
from pymongo import MongoClient
from core.settings import config
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import re
from confluent_kafka import Producer
from fluent import sender, event
from io import BytesIO
from datetime import datetime

kafka_internal_producer = Producer(config['KAFKA_INTERNAL_PRODUCER_CONFIGURATION'])

# Create Fluentd instance for integrations service
sender.setup(config["FLUENT_CHANNEL"], host=config["FLUENT_HOST"], port=config["FLUENT_PORT"])


# Emit event message in fluentd
def produce_to_fluentd(payload):
    event.Event('follow', payload)


def encode_string(string):
    return base64.b32encode(string.encode('utf8')).decode('utf8')


def decode_string(encoded_value):
    return base64.b32decode(encoded_value.encode('utf8')).decode('utf8')


def integrationsHandler(payload):
    try:
        produce_to_fluentd(payload)
    except Exception as e:
        pass


def get_logger(name, log_file, log_level="INFO"):
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(msecs)d - %(funcName)s - %(lineno)d : %(levelname)s : %(message)s')
    fh = logging.FileHandler(filename=log_file)
    fh.setLevel(log_level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def validate_params(endpoint, data):
    required_fields = config['REQUIRED_FIELDS_MAP'].get(endpoint)
    for field in required_fields:
        if data.get(field, None) is None:
            return False
    return True


def validate_params_by_model(payload, schema) -> bool:
    try:
        validate(instance=payload, schema=schema)
        return True
    except ValidationError:
        return False
    
    
def converter_datetime(o):
    if isinstance(o, datetime):
        return o.strftime("%Y-%m-%dT%H:%M:%S")

def response(status, title, data={}, error={}):
    return json.dumps({
        "status": status,
        "title": title,
        "error": error,
        "data": data
    }, default = converter_datetime)


def get_client(host=None,
               replicaSet=config['MONGO_REPLICA_SET']):
    if host is None:
        host = [config['MONGO_PRIMARY_DB_URL'], config['MONGO_SECONDARY_DB_URL']]
    return MongoClient(host=host, replicaSet=replicaSet)


def get_redis_instance():
    return redis.StrictRedis(host=config['REDIS_HOST'], port=config['REDIS_PORT'])


def generate_id_or_pwd(length=10, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789'):
    return ''.join(random.choice(allowed_chars) for _ in range(length))


def generate_sharable_id(length=10, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    return ''.join(random.choice(allowed_chars) for _ in range(length))


def generate_survey_fillout_link(public_survey_id, user):
    if public_survey_id is None or user is None:
        return None
    # Generate link base on user account
    survey_fillout_link = user["subdomain"] + config['SURVEY_FILLOUT_DOMAIN_BASE_URL'] + config[
        'SURVEY_FILLOUT_PATH'] + "/" + public_survey_id
    return survey_fillout_link


def generate_qr(gen_code, logger):
    try:
        qr_img = qrcode.make(gen_code)
        img = qr_img.get_image()
        image_read = img.tobytes()
        image_64_encode = base64.encodestring(image_read)
        logger.info("[BACKEND]: QR code generated for the code " + gen_code)
        return image_64_encode
    except OSError:
        logger.error("[BACKEND]: Failed to generate qrcode for the code " + gen_code)
        return ""


# this helper is used to generate qrcode and return it in base64 format
def qrcode_generator(text: str, logger: Logger) -> str:
    logger.info(f"The text you want to convert in qrcode is : {text}")
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=4,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image()
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str


# This method allow to check if an key exist redis cache
def get_customer_database_from_redis(key: str, redis_instance):
    if redis_instance.exists(key):
        return json.loads(redis_instance.get(key).decode('utf-8'))
    return None


def strip_html_tag_from_string(text: str) -> str:
    clean = re.compile('<.*?>|&#\d*;')
    return re.sub(clean, '', text)


def produce_to_mail_kafka(message):
    kafka_internal_producer.produce(config['KAFKA_MAIL_SERVICE_TOPIC'], json.dumps(message).encode('utf-8'))
    kafka_internal_producer.poll(0)


def convert(data):
    if isinstance(data, bytes):  return data.decode('utf-8')
    if isinstance(data, dict):   return dict(map(convert, data.items()))
    if isinstance(data, tuple):  return map(convert, data)
    return data


def get_license_right_based_by_key(curr_license: dict, key: str) -> dict:
    result = filter(lambda x: x['key'] == key, curr_license['license_rights'])
    return dict(*result)


def convert_timestamp_to_str_datetime(timestamp: float) -> str:
    dt_object = datetime.fromtimestamp(timestamp)
    return dt_object.strftime("%Y-%m-%d %H:%M:%S")
