import sys

sys.path.append("/usr/src/app/api")
from utils import helpers as hp
from pymongo.errors import AutoReconnect, DuplicateKeyError, ConnectionFailure, OperationFailure
import pymongo
import datetime
from core.settings import config

# Get mongodb cluster connection instance
client = hp.get_client()
logger = hp.get_logger(config['LOGGER']['DB_CALLER'], config['LOG_FILES']['DB_CALLER_LOG'])


def find_with_criteria(**kwargs):
    try:
        db = getattr(client, kwargs.get(config["ATTR_DATABASE"]))
        db.authenticate(kwargs.get(config["ATTR_USERNAME"]), kwargs.get(config["ATTR_PWD"]),
                        source=kwargs.get(config["ATTR_DATABASE"]))
        return get_list(db, kwargs.get(config["ATTR_COLLECTION"]),
                        kwargs.get(config["ATTR_PROJECTION"], {'_id': False, 'id': False, 'created_at': False}),
                        kwargs.get(config["ATTR_CRITERIA"], {}), kwargs.get(config["ATTR_SORT"], [('created_at', 1)]),
                        kwargs.get(config["ATTR_LIMIT"], 0),
                        kwargs.get(config["ATTR_PAGINATOR"], None)), True
    except (ConnectionFailure, AutoReconnect, OperationFailure) as e:
        logger.info("find_with_criteria method error : %s" % e)
        return str(e), False


def find_one(database, username, pwd, collection, criteria, projection):
    try:
        db = getattr(client, database)
        db.authenticate(username, pwd, source=database)
        result = db[collection].find_one(criteria, projection)
        return map_fornat_date_type(result) if result else result, True
    except (ConnectionFailure, AutoReconnect, OperationFailure) as e:
        return str(e), False


def update_one(**kwargs):
    try:
        db = getattr(client, kwargs.get(config["ATTR_DATABASE"]))
        db.authenticate(kwargs.get(config["ATTR_USERNAME"]), kwargs.get(config["ATTR_PWD"]),
                        source=kwargs.get(config["ATTR_DATABASE"]))
        date = datetime.datetime.now()
        if kwargs.get(config["ATTR_TYPE"], config["ATTR_TYPE_DEFAULT_VALUE"]) == config["ATTR_TYPE_DEFAULT_VALUE"]:
            kwargs.get(config["ATTR_PARAM"])['updated_at'] = date
        db[kwargs.get(config["ATTR_COLLECTION"])].update_one(kwargs["criteria"], {
            kwargs.get(config["ATTR_TYPE"], config["ATTR_TYPE_DEFAULT_VALUE"]): kwargs.get(config["ATTR_PARAM"])})
        if kwargs.get(config["ATTR_LISTBACK"]):
            return get_list(db, kwargs.get(config["ATTR_COLLECTION"])), True
        else:
            return 1, True
    except DuplicateKeyError:
        return 0, True
    except (ConnectionFailure, AutoReconnect, OperationFailure) as e:
        return str(e), False


def update_many(database, username, pwd, collection, criteria, updateR, multi=True):
    try:
        db = getattr(client, database)
        db.authenticate(username, pwd, source=database)
        if multi:
            db[collection].update_many(criteria, updateR)
        else:
            db[collection].update_one(criteria, updateR)
        return 1, True
    except DuplicateKeyError:
        return 0, True
    except (ConnectionFailure, AutoReconnect, OperationFailure) as e:
        return str(e), False


def delete_one(database, username, pwd, collection, criteria, listback=True):
    try:
        db = getattr(client, database)
        db.authenticate(username, pwd, source=database)
        db[collection].delete_one(criteria)
        if listback:
            return get_list(db, collection), True
        else:
            return 1, True
    except (ConnectionFailure, AutoReconnect, OperationFailure) as e:
        return str(e), False


def insert_one(database, username, pwd, collection, data, listback=True):
    try:
        db = getattr(client, database)
        db.authenticate(username, pwd, source=database)
        date = datetime.datetime.now()
        data['created_at'] = date
        data['updated_at'] = date
        db[collection].insert_one(data)
        if listback:
            return get_list(db, collection), True
        else:
            return data["viewid"] if "viewid" in data else 1, True
    except DuplicateKeyError:
        return 0, True
    except (ConnectionFailure, AutoReconnect, OperationFailure) as e:
        return str(e), False


def insert_many(database, username, pwd, collection, data, listback=False):
    try:
        db = getattr(client, database)
        db.authenticate(username, pwd, source=database)
        db[collection].insert_many(data)
        if listback:
            return get_list(db, collection), True
        else:
            return 1, True
    except DuplicateKeyError:
        return 0, True
    except (ConnectionFailure, AutoReconnect, OperationFailure, Exception) as e:
        return str(e), False


def get_list(db, collection, projection={'_id': False, 'id': False}, criteria={}, sort=[('created_at', -1)], limit=0,
             paginator=None):
    result = []
    if paginator is None:
        cursor = db[collection].find(criteria, projection).sort([("created_at", pymongo.DESCENDING)]).limit(limit)
    else:
        cursor = db[collection].find(criteria, projection).skip(paginator["skip"]).limit(paginator["limit"])
    for element in cursor:
        result.append(map_fornat_date_type(element))
    logger.info("get_list result : %s" % result)
    return result


def count(database, username, pwd, collection, criteria={}):
    try:
        db = getattr(client, database)
        db.authenticate(username, pwd, source=database)
        return db[collection].count(criteria), True
    except (ConnectionFailure, AutoReconnect, OperationFailure) as e:
        return str(e), False


def get_all_element(database, username, pwd, collection, criteria={}):
    try:
        db = getattr(client, database)
        db.authenticate(username, pwd, source=database)
        return get_list(db, collection), True
    except (ConnectionFailure, AutoReconnect, OperationFailure) as e:
        return str(e), False


def get_next_sequence(database, username, pwd, collection):
    try:
        db = getattr(client, database)
        db.authenticate(username, pwd, source=database)
        return db['counters'].find_and_modify(query={'id': 'userid', 'collection': collection},
                                              update={'$inc': {'seq': 1}}, new=True).get('seq')
    except ConnectionFailure:
        return -2
    except AutoReconnect:
        return -2
    except OperationFailure:
        return -1


def aggregate_data(database, username, pwd, collection, pipeline):
    try:
        db = getattr(client, database)
        db.authenticate(username, pwd, source=database)

        response = []
        for agg_response in db[collection].aggregate(pipeline):
            response.append(agg_response)

        return response, True

    except (ConnectionFailure, AutoReconnect, OperationFailure) as e:
        return str(e), False


def map_fornat_date_type(element):
    for key in element:
        if isinstance(element[key], datetime.datetime):
            element[key] = element[key].strftime("%Y-%m-%dT%H:%M:%S")
        format_answers_date(key, element)
    return element


def format_answers_date(key, element):
    if key == config["SURVEY_ATTR_ANSWERS"]:
        for answer in element[key]:
            for k in answer:
                if isinstance(answer[k], datetime.datetime):
                    # answer[k] = answer[k].strftime("%Y-%m-%d")
                    answer[k] = datetime.datetime.timestamp(answer[k])


def check_If_collection_exist(database, username, pwd, collection):
    try:
        db = getattr(client, database)
        db.authenticate(username, pwd, source=database)
        return collection in db.list_collection_names(), True
    except (ConnectionFailure, AutoReconnect, OperationFailure) as e:
        return str(e), False


def add_new_collection_to_customer_db(database, username, pwd, collection):
    try:
        db = getattr(client, database)
        db.authenticate(username, pwd, source=database)
        db['counters'].insert_one({'id': "userid", 'collection': collection, 'seq': 0})
        db.logout()
        return 1, True
    except (ConnectionFailure, AutoReconnect, OperationFailure) as e:
        return str(e), False
