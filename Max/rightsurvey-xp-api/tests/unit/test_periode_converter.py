from unittest import TestCase
from api.utils.periode_converter import PeriodeConverter
from datetime import date, datetime, time
import datetime as dt


class TestPeriodeConverter(TestCase):

    def test_converter_last_7_days(self):
        start_date, end_date = PeriodeConverter.converter('last 7 days')
        excepted_start_date = datetime.combine(date.today() - dt.timedelta(6), time.min)
        excepted_end_date = datetime.combine(date.today(), time.max)
        self.assertEqual(start_date, excepted_start_date)
        self.assertEqual(end_date, excepted_end_date)

    def test_converter_today(self):
        start_date, end_date = PeriodeConverter.converter('today')
        excepted_start_date = datetime.combine(date.today(), time.min)
        excepted_end_date = datetime.combine(date.today(), time.max)
        self.assertEqual(start_date, excepted_start_date)
        self.assertEqual(end_date, excepted_end_date)

    def test_converter_last_30_days(self):
        start_date, end_date = PeriodeConverter.converter('last 30 days')
        excepted_start_date = datetime.combine(date.today() - dt.timedelta(29), time.min)
        excepted_end_date = datetime.combine(date.today(), time.max)
        self.assertEqual(start_date, excepted_start_date)
        self.assertEqual(end_date, excepted_end_date)

    def test_converter_custom_days_with_end_date_is_none(self):
        start_date, end_date = PeriodeConverter.converter('custom', started_date='10/05/2021')
        excepted_start_date = datetime.combine(datetime.strptime('10/05/2021', '%d/%m/%Y'), time.min)
        self.assertEqual(start_date, excepted_start_date)
        self.assertEqual(end_date, None)

    def test_converter_custom_days_with_start_date_is_none(self):
        start_date, end_date = PeriodeConverter.converter('custom', ended_date='10/05/2021')
        excepted_end_date = datetime.combine(datetime.strptime('10/05/2021', '%d/%m/%Y'), time.max)
        self.assertEqual(start_date, None)
        self.assertEqual(end_date, excepted_end_date)