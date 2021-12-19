import sys

sys.path.append("/usr/src/app/api")
import datetime
from datetime import datetime as dt


class PeriodeConverter:

    @staticmethod
    def converter(periode: str, started_date=None, ended_date=None) -> tuple:

        if periode == "today":
            start_date = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
            end_date = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
            return start_date, end_date

        if periode == 'last 7 days':
            end_date = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
            start_date = datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=6),
                                                   datetime.time.min)
            return start_date, end_date

        if periode == 'last 30 days':
            end_date = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
            start_date = datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=29),
                                                   datetime.time.min)
            return start_date, end_date

        if periode == "custom":
            if started_date and ended_date:
                start_date = datetime.datetime.combine(dt.strptime(started_date, '%d/%m/%Y'), datetime.time.min)
                end_date = datetime.datetime.combine(dt.strptime(ended_date, '%d/%m/%Y'), datetime.time.max)
                return start_date, end_date

            if started_date and not ended_date:
                start_date = datetime.datetime.combine(dt.strptime(started_date, '%d/%m/%Y'), datetime.time.min)
                return start_date, None

            if not started_date and ended_date:
                end_date = datetime.datetime.combine(dt.strptime(ended_date, '%d/%m/%Y'), datetime.time.max)
                return None, end_date
