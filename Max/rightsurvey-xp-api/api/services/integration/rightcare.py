import sys

sys.path.append("/usr/src/app/api")
from core.settings import config
from core.dbutils import get_list, get_one, edit_one
from logging import Logger
from third_party.rc_services import RightCareServices


def get_list_of_template_surveys(payload: dict, logger: Logger) -> tuple:
    try:
        database = payload['database']
        collection = payload['collection']
        logger.info(f'database informations : {database}')
        template_surveys: tuple = get_list(database=database["dbname"], username=database["dbuser"],
                                           pwd=database["dbpassword"],
                                           collection=collection,
                                           criteria={'type': 'template', 'status': 1, "parent": {"$exists": False},
                                                     "settings.connectRightcare": False},
                                           sort=[('created_date', -1)],
                                           projection={'viewid': 1, "name": 1, "answers": 1})
        if not (template_surveys[1] and template_surveys[0]):
            return f'We are not able to get list of template surveys', False

        # Map method used to handle list mapping
        def list_template_surveys_mapper(x: dict):
            x['total_respondent'] = len(x["answers"]) if "answers" in x else 0
            del x['_id']
            if "answers" in x: del x['answers']
            return x

        return list(map(list_template_surveys_mapper, template_surveys[0])), True
    except Exception as e:
        logger.info(f"An exception occured in get_list_of_template_surveys method with this error : {e}")
        return f"An exception occured with following details : {e}", False


def save_configuration(payload: dict, service: RightCareServices, logger: Logger) -> tuple:
    try:
        header: dict = {'publickey': payload.get('publickey'), 'apisid': payload.get('apisid'),
                        'sessionid': payload.get('sessionid')}
        viewids: list = payload.get('viewids')
        priority: int = payload.get('priority')
        agent: str = payload.get('agent')
        database = payload['database']
        logger.info(f'header == {header}')
        for viewid in viewids:
            survey, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'], 'surveys',
                                {'viewid': viewid})
            logger.info(f'survey == {survey}')
            status, resp_data = service.create_configuration(
                {'survey_id': viewid, 'title': survey.get('name'), 'priority_id': priority, 'assigned_agent_id': agent},
                header)
            logger.info(f'status : {status} - data : {resp_data}')
            if status:
                edit_one(database=database["dbname"], username=database["dbuser"], pwd=database["dbpassword"],
                                collection='surveys', criteria={'viewid': viewid},
                                param={"settings.connectRightcare": True}, listback=False)
                edit_one(database=config["PUBLIC_DB_NAME"], username=config["PUBLIC_DB_USER"],
                         pwd=config["PUBLIC_DB_PWD"], collection="surveys_publish", criteria={'viewid': viewid},
                         param={"settings.connectRightcare": True}, type='$set', listback=False)

        return None, True
    except Exception as e:
        logger.info(f"An exception occured in save_configuration method with this error : {e}")
        return f"An exception occured with following details : {e}", False


def update_configuration(payload: dict, service: RightCareServices, logger: Logger) -> tuple:
    try:
        header: dict = {'publickey': payload.get('publickey'), 'apisid': payload.get('apisid'),
                        'sessionid': payload.get('sessionid')}
        viewid: str = payload.get('viewid')
        priority: int = payload.get('priority')
        agent: str = payload.get('agent')
        database = payload['database']
        survey, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'], 'surveys',
                            {'viewid': viewid})
        status, resp_data = service.update_configuration(viewid, {'title': survey.get('name'), 'priority_id': priority,
                                                                  'assigned_agent_id': agent},
                                                         header)
        logger.info(f'status : {status} - data : {resp_data}')
        if not status: return f'Something was wrong from the update processing', False
        return None, True
    except Exception as e:
        logger.info(f"An exception occured in update_configuration method with this error : {e}")
        return f"An exception occured with following details : {e}", False


def delete_configuration(payload: dict, service: RightCareServices, logger: Logger) -> tuple:
    try:
        database: dict = payload.get('database')
        header: dict = {'publickey': payload.get('publickey'), 'apisid': payload.get('apisid'),
                        'sessionid': payload.get('sessionid')}
        viewid: str = payload.get('viewid')
        status = service.delete_configuration(viewid, header)
        logger.info(f'status : {status}')
        survey, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'], 'surveys',
                            {"viewid": viewid})
        if status:
            edit_one(database=database["dbname"], username=database["dbuser"], pwd=database["dbpassword"],
                     collection='surveys', criteria={'viewid': viewid},
                     param={"settings.connectRightcare": False}, listback=False)
            if survey['status'] == 1:
                edit_one(database=config["PUBLIC_DB_NAME"], username=config["PUBLIC_DB_USER"],
                         pwd=config["PUBLIC_DB_PWD"], collection="surveys_publish", criteria={'viewid': viewid},
                         param={"settings.connectRightcare": False}, type='$set', listback=False)

        if not status: return f'Something was wrong from the update processing', False
        return None, True
    except Exception as e:
        logger.info(f"An exception occured in delete_configuration method with this error : {e}")
        return f"An exception occured with following details : {e}", False


def check_connection_to_rightcare(database: dict, logger: Logger) -> tuple:
    try:
        logger.info(f'database : {database}')
        rightcare_template_surveys, _ = get_list(database=database["dbname"],
                                                 username=database["dbuser"],
                                                 pwd=database["dbpassword"],
                                                 collection='surveys',
                                                 criteria={
                                                     'type': 'template',
                                                     'status': 1,
                                                     'parent': {'$exists': False},
                                                     'settings.connectRightcare': True
                                                 },
                                                 sort=[('created_date', -1)]
                                                 )
        if len(rightcare_template_surveys) == 0: return {'connected': False,
                                                         'count': len(rightcare_template_surveys)}, True
        return {'connected': True, 'count': len(rightcare_template_surveys)}, True
    except Exception as e:
        logger.info(f"An exception occured in check_connection_to_rightcare method with this error : {e}")
        return f"An exception occured with following details : {e}", False


def get_list_surveys_connect_to_rightcare(payload: dict, service: RightCareServices, logger: Logger) -> tuple:
    try:
        database: dict = payload.get('database')
        header: dict = {'publickey': payload.get('publickey'), 'apisid': payload.get('apisid'),
                        'sessionid': payload.get('sessionid')}
        logger.info(f'database : {database}')
        status, resp_data = service.get_list_configuration(header)
        if not status:
            return 'There are some issues on the rightcare api which return a config list', False
        logger.info(f'List of config get from rightcare {resp_data}')
        rightcare_template_surveys, _ = get_list(database=database["dbname"],
                                                 username=database["dbuser"],
                                                 pwd=database["dbpassword"],
                                                 collection='surveys',
                                                 criteria={
                                                     'type': 'template',
                                                     'status': 1,
                                                     'parent': {'$exists': False},
                                                     'settings.connectRightcare': True
                                                 },
                                                 sort=[('created_date', -1)],
                                                 projection={'viewid': 1, "name": 1, "answers": 1}
                                                 )

        def list_template_surveys_mapper(x: dict):
            rightcare_data = resp_data['data']
            logger.info(f'RightCare data : {rightcare_data}')
            y = dict(*filter(lambda z: z['survey_id'] == x['viewid'], resp_data['data']))
            logger.info(f'y = {y}')
            x['priority'] = y['priority_id']
            x['assigned_agent'] = y['assigned_agent_id']
            x['total_respondent'] = len(x["answers"]) if "answers" in x else 0
            del x['_id']
            if "answers" in x: del x['answers']
            return x

        return list(map(list_template_surveys_mapper, rightcare_template_surveys)), True
    except Exception as e:
        logger.info(f"An exception occured in get_list_surveys_connect_to_rightcare method with this error : {e}")
        return f"An exception occured with following details : {e}", False


def disconnect_specific_survey(payload: dict, service: RightCareServices, logger: Logger) -> tuple:
    try:
        viewid: str = payload.get('viewid')
        database: dict = payload.get('database')
        header: dict = {'publickey': payload.get('publickey'), 'apisid': payload.get('apisid'),
                        'sessionid': payload.get('sessionid')}
        status = service.delete_configuration(viewid, header)
        survey, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'], 'surveys',
                            {"viewid": viewid})
        if status:
            edit_one(database=database["dbname"], username=database["dbuser"], pwd=database["dbpassword"],
                     collection='surveys', criteria={'viewid': viewid}, param={"settings.connectRightcare": False},
                     listback=False)
            if survey['status'] == 1:
                edit_one(database=config["PUBLIC_DB_NAME"], username=config["PUBLIC_DB_USER"],
                         pwd=config["PUBLIC_DB_PWD"], collection="surveys_publish", criteria={'viewid': viewid},
                         param={"settings.connectRightcare": False}, type='$set', listback=False)
            return {'disconnected': True}, True
        return {'disconnected': False}, False
    except Exception as e:
        logger.info(f"An exception occured in disconnect_specific_survey method with this error : {e}")
        return f"An exception occured with following details : {e}", False


def disconnect_all_surveys(payload: dict, service: RightCareServices, logger: Logger) -> tuple:
    try:
        database: dict = payload.get('database')
        header: dict = {'publickey': payload.get('publickey'), 'apisid': payload.get('apisid'),
                        'sessionid': payload.get('sessionid')}
        rightcare_template_surveys, _ = get_list(database=database["dbname"],
                                                 username=database["dbuser"],
                                                 pwd=database["dbpassword"],
                                                 collection='surveys',
                                                 criteria={
                                                     'type': 'template',
                                                     'status': 1,
                                                     'parent': {'$exists': False},
                                                     'settings.connectRightcare': True
                                                 }
                                                 )
        viewids: list = list(map(lambda x: x['viewid'], rightcare_template_surveys))
        for viewid in viewids:
            status = service.delete_configuration(viewid, header)
            survey, _ = get_one(database['dbname'], database['dbuser'], database['dbpassword'], 'surveys',
                                {"viewid": viewid})
            if status:
                edit_one(database=database["dbname"], username=database["dbuser"], pwd=database["dbpassword"],
                                collection='surveys', criteria={'viewid': viewid},
                                param={"settings.connectRightcare": False}, listback=False)
                if survey['status'] == 1:
                    edit_one(database=config["PUBLIC_DB_NAME"], username=config["PUBLIC_DB_USER"],
                             pwd=config["PUBLIC_DB_PWD"], collection="surveys_publish", criteria={'viewid': viewid},
                             param={"settings.connectRightcare": False}, type='$set', listback=False)
        return {'disconnected': True}, True
    except Exception as e:
        logger.info(f"An exception occured in disconnect_all_surveys method with this error : {e}")
        return f"An exception occured with following details : {e}", False


def create_ticket_for_selected_survey(payload: dict, service: RightCareServices, logger: Logger):
    try:
        collection = payload["collection"]
        viewid = payload["viewid"]
        survey, _ = get_one(config["PUBLIC_DB_NAME"], config["PUBLIC_DB_USER"], config["PUBLIC_DB_PWD"], collection,
                            {"viewid": viewid})
        if not survey:
            return f'Oups ! the survey with viewid : {viewid} was not found', False
        data: dict = {
            "publickey": survey["publickey"],
            "survey_id": viewid,
            "firstname": payload["firstname"],
            "email": payload["email"],
            "phone": payload["phone"],
            "message": payload["message"]
        }
        status, resp_data = service.create_ticket(data)
        logger.info(f'status = {status}')
        logger.info(f'resp_data = {resp_data}')
        if not status:
            error_msg = resp_data['message'] if resp_data.get(
                'message') else f'Oups ! we are not able to create new ticket on rightcare'
            return error_msg, False
        return None, True
    except Exception as e:
        logger.info(f"An exception occured in create_ticket_for_selected_survey method with this error : {e}")
        return f"An exception occured with following details : {e}", False


def get_plateform_agents(payload: dict, service: RightCareServices, logger: Logger) -> tuple:
    header: dict = {'publickey': payload.get('publickey'), 'apisid': payload.get('apisid'),
                    'sessionid': payload.get('sessionid')}
    logger.info(f'header = {header}')
    status, data = service.get_customer_agent_list(header)
    if not status:
        return True, []
    logger.info(f'rightcare plateform agent list : {data}')
    return True, list(
        map(lambda r: {'id': r['user_id'], 'name': f'{r["lastname"]} {r["firstname"]}', 'image': ''}, data))
