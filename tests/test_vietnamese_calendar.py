"""Archived v3 adapter regression tests; not the application calendar.

The active v4 calendar is covered by test_beijing_calendar.py.
"""
import unittest
from datetime import date, datetime

from calendar_adapter import CalendarError, LunarDate, VietnameseCalendar, resolve_maihoa
from calendar_adapter.vietnamese import _solar_to_lunar


class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.calendar = VietnameseCalendar()

    def assert_code(self, code, operation, *args):
        with self.assertRaises(CalendarError) as raised:
            operation(*args)
        self.assertEqual(raised.exception.code, code)

    def test_published_hnd_1984_dates(self):
        # Explicit dates in the source article, not outputs of this adapter.
        self.assertEqual(self.calendar.to_lunar(date(1984, 1, 3)), LunarDate(1983, 12, 1))
        self.assertEqual(self.calendar.to_lunar(date(1984, 2, 2)), LunarDate(1984, 1, 1))
        self.assertEqual(self.calendar.to_lunar(date(1984, 11, 23)), LunarDate(1984, 11, 1))

    def test_published_hnd_2004_leap_month(self):
        self.assertEqual(self.calendar.to_lunar(date(2004, 3, 21)), LunarDate(2004, 2, 1, True))
        self.assertEqual(self.calendar.to_lunar(date(2004, 4, 18)), LunarDate(2004, 2, 29, True))
        self.assertEqual(self.calendar.to_lunar(date(2004, 4, 19)), LunarDate(2004, 3, 1))

    def test_utc7_and_utc8_differ_away_from_midnight(self):
        # NASA's January 1968 new moon falls on Jan 29 UTC+7 / Jan 30 UTC+8.
        self.assertEqual(self.calendar.to_lunar(date(1968, 1, 29)).day, 1)
        self.assertEqual(_solar_to_lunar(date(1968, 1, 29), 8).day, 30)
        self.assertEqual(self.calendar.to_lunar(date(1968, 1, 30)).day, 2)
        self.assertEqual(_solar_to_lunar(date(1968, 1, 30), 8).day, 1)

    def test_buffer_endpoints_round_trip(self):
        for value in [date(1949, 12, 1), date(2031, 1, 31)]:
            with self.subTest(value=value):
                self.assertEqual(self.calendar.to_solar(self.calendar.to_lunar(value)), value)

    def test_outside_internal_buffer(self):
        for value in [date(1949, 11, 30), date(2031, 2, 1)]:
            self.assert_code("CALENDAR_LOOKUP_OUT_OF_RANGE", self.calendar.to_lunar, value)

    def test_invalid_lunar_days_and_leap_months(self):
        self.assert_code("INVALID_LUNAR_DATE", self.calendar.to_solar, LunarDate(2004, 2, 30, True))
        self.assert_code("INVALID_LEAP_MONTH", self.calendar.to_solar, LunarDate(2004, 3, 1, True))
        self.assert_code("INVALID_LEAP_MONTH", self.calendar.to_solar, LunarDate(1984, 1, 1, True))

    def test_input_types(self):
        self.assert_code("INVALID_LUNAR_DATE", LunarDate, 2026, True, 1)
        self.assert_code("INVALID_LUNAR_DATE", LunarDate, 2026, 1, 1, 1)
        self.assert_code("INVALID_SOLAR_DATE", self.calendar.to_lunar, datetime(2026, 1, 1))

    def test_month_end_rolls_all_fields_at_23(self):
        civil = datetime.fromisoformat("2024-02-09T23:00:00+07:00")
        result = resolve_maihoa(civil, datetime(2024, 2, 9, 23))
        self.assertEqual(result["effective_date"], "2024-02-10")
        self.assertEqual(result["civil_lunar"], {"year": 2023, "month": 12, "day": 30, "is_leap_month": False})
        self.assertEqual(result["maihoa_inputs"], {"Y": 5, "M": 1, "D": 1, "H": 1})
        self.assertEqual(result["utc_instant"], "2024-02-09T16:00:00Z")

    def test_tst_boundary_not_civil_clock_boundary(self):
        civil = datetime.fromisoformat("2024-02-09T23:02:00+07:00")
        result = resolve_maihoa(civil, datetime(2024, 2, 9, 22, 59, 59))
        self.assertEqual(result["effective_date"], "2024-02-09")
        self.assertEqual(result["maihoa_inputs"], {"Y": 4, "M": 12, "D": 30, "H": 12})

    def test_upstream_tst_may_cross_input_year_bounds(self):
        birth = resolve_maihoa(datetime.fromisoformat("1950-01-01T00:05:00+07:00"), datetime(1949, 12, 31, 23, 55), "birth")
        self.assertEqual(birth["effective_date"], "1950-01-01")
        casting = resolve_maihoa(datetime.fromisoformat("2030-12-31T23:55:00+07:00"), datetime(2031, 1, 1, 0, 5))
        self.assertEqual(casting["effective_date"], "2031-01-01")

    def test_input_range_rejected_before_tst(self):
        self.assert_code("INPUT_OUT_OF_RANGE", resolve_maihoa, datetime.fromisoformat("2031-01-01T00:00:00+07:00"), datetime(2030, 12, 31, 23, 50))
        self.assert_code("INPUT_OUT_OF_RANGE", resolve_maihoa, datetime.fromisoformat("1949-12-31T23:55:00+07:00"), datetime(1950, 1, 1), "birth")

    def test_timezone_and_tst_are_separate(self):
        self.assert_code("INVALID_INPUT_TIMEZONE", resolve_maihoa, datetime(2026, 1, 1), datetime(2026, 1, 1))
        self.assert_code("INVALID_INPUT_TIMEZONE", resolve_maihoa, datetime.fromisoformat("2026-01-01T00:00:00+08:00"), datetime(2026, 1, 1))
        self.assert_code("INVALID_TST_CLOCK", resolve_maihoa, datetime.fromisoformat("2026-01-01T00:00:00+07:00"), datetime.fromisoformat("2026-01-01T00:00:00+07:00"))
        self.assert_code("INVALID_TST_CLOCK", resolve_maihoa, datetime.fromisoformat("2026-01-01T00:00:00+07:00"), datetime(2028, 1, 1))


if __name__ == "__main__":
    unittest.main()
