import sys

sys.path.append("/usr/src/app/api")
from datetime import datetime


class DatetimeConverter:

    @staticmethod
    def map_datetime_to_timestamp(elements: list) -> list:
        for elm in elements:
            for key in elm:
                if isinstance(elm[key], datetime): elm[key] = datetime.timestamp(elm[key])
        return elements