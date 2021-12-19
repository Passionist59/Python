import sys

sys.path.append("/usr/src/app/api")
from datetime import datetime
from core.settings import config


class QueryBuilder:

    @staticmethod
    def match_query_for_date_interval(start_date: datetime, end_date: datetime, query_field: str) -> dict:
        if start_date and end_date:
            return {config["PIPELINE_ATTR_MATCH"]: {query_field: {"$gte": start_date, "$lte": end_date}}}
        if start_date and not end_date:
            return {config["PIPELINE_ATTR_MATCH"]: {query_field: {"$gte": start_date}}}
        if not start_date and end_date:
            return {config["PIPELINE_ATTR_MATCH"]: {query_field: {"$lte": end_date}}}
