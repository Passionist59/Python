import sys

sys.path.append("/usr/src/app/api")
from core.dbcall import find_with_criteria, find_one, update_one, update_many, delete_one, insert_one, count, \
    get_next_sequence, aggregate_data, check_If_collection_exist, add_new_collection_to_customer_db
from utils import helpers as hp


def get_list(**kwargs):
    return find_with_criteria(**kwargs)


def get_one(database, username, pwd, collection, criteria, projection={'_id': False, 'id': False, 'created_date': False}):
    return find_one(database, username, pwd, collection, criteria, projection)


def edit_one(**kwargs):
    return update_one(**kwargs)


def edit_many(database, username, pwd, collection, criteria, data, mult=True):
    return update_many(database, username, pwd, collection, criteria, data, mult)


def delete(database, username, pwd, collection, criteria, listback=True):
    return delete_one(database, username, pwd, collection, criteria, listback)


def add(database, username, pwd, collection, data, listback=True):
    id = get_next_sequence(database, username, pwd, collection)
    if id >= 0:
        data['id'] = id
        data['viewid'] = hp.generate_id_or_pwd(30)
        return insert_one(database, username, pwd, collection, data, listback)
    else:
        return "Cannot generate id", False


def count_data(database, username, pwd, collection, criteria={}):
    return count(database, username, pwd, collection, criteria)


def execute_aggregation(database, username, pwd, collection, pipeline):
    return aggregate_data(database, username, pwd, collection, pipeline)


def add_to_public(database, username, pwd, collection, data, listback=True):
    return insert_one(database, username, pwd, collection, data, listback)


def check_collection_exists(database, username, pwd, collection):
    return check_If_collection_exist(database, username, pwd, collection)


def add_collection(database, username, pwd, collection):
    return add_new_collection_to_customer_db(database, username, pwd, collection)
