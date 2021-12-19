import sys

sys.path.append("/usr/src/app/api")
from utils import helpers as hp
from core.settings import config
from pymongo.errors import ConnectionFailure, OperationFailure

# Get mongodb cluster connection instance
client = hp.get_client()


def generate_database(database, company, logger):
    user_string = '(' + company + ')'
    username = database + '_user'
    logger.info(user_string + " Setup database : " + database)
    try:
        db = client.admin
        db.authenticate(config["MONGO_ADMIN_DB_USER"], config["MONGO_ADMIN_DB_PASSWORD"],
                        source=config["MONGO_ADMIN_DB_NAME"])
        if database in client.database_names():
            logger.info(user_string + " Database creation FAILED because already exists")
            return 'Database already exists'
        mydb = getattr(client, database)
        pwd = hp.generate_id_or_pwd(15)
        mydb.add_user(username, pwd, roles=[{'role': 'dbOwner', 'db': database}])
        mydb.authenticate(username, pwd, source=database)
        logger.info(user_string + "  Database user creation : '" + username + "' and pwd : '" + pwd + "' : SUCCESS")
        for collection in config["MONGO_DB_DEFAULT_COLLECTIONS"]:
            mydb['counters'].insert_one({'id': "userid", 'collection': collection, 'seq': 0})
        mydb.logout()
        db.logout()
        logger.info(user_string + '  Database : ' + database + ' setup successfully')
        return {'db_name': database, 'db_password': pwd, 'db_type': "MONGO", 'db_user': username, 'db_host': '',
                'db_port': '27017'}
    except OperationFailure as exc:
        logger.error(user_string + ' Database setup failed with error : ' + str(exc))
        client.drop_database(database)
        return str(exc)

    except ConnectionFailure as exc1:
        logger.error(user_string + ' Database setup failed with error : ' + str(exc1))
        client.drop_database(database)
        return str(exc1)
