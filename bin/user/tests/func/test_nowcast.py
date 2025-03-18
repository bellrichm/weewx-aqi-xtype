#    Copyright (c) 2023-2025 Rich Bell <bellrichm@gmail.com>
#    See the file LICENSE.txt for your full rights.

# pylint: disable=missing-docstring

import random
import string
import time
import unittest

import mock

import user.aqitype

def random_string(length=32):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(length)]) # pylint: disable=unused-variable

def min_max(values):
    min_value = float('inf')
    max_value = -float('inf')
    for value in values:
        if value is not None:
            if value < min_value:
                min_value = value
            if value > max_value:
                max_value = value
    return min_value, max_value

class TestNowCastCalculate(unittest.TestCase):
    def setUp(self):
        self.mock_logger = mock.Mock(spec=user.aqitype.Logger)

    def _populate_time_stamps(self, current_hour, count):
        time_stamps = []
        index = 0
        while index < count:
            time_stamps.append(current_hour - (index - 1) * 3600)
            index += 1

        return time_stamps

    def test_incomplete_data(self):
        now = time.time()
        current_hour =  int(now / 3600) * 3600

        data = [random.uniform(0, 700)]
        timestamps = self._populate_time_stamps(current_hour, len(data))

        aqi_type = random_string()
        # ToDo: optimize. Eliminate need _populate_time_stamps call (above)?
        records = []
        i = 0
        for concentration in data:
            records.append((timestamps[i], concentration))
            i += 1

        SUT = user.aqitype.NowCast(self.mock_logger, 0, None, None)

        start_vec, stop_vec, aqi_vec = SUT.calculate(aqi_type, iter(records))

        self.assertEqual(start_vec, [timestamps[0]])
        self.assertEqual(stop_vec, [timestamps[0] + 3600])
        self.assertEqual(aqi_vec, [None])

    def test_beginning_missing_data(self):
        now = time.time()
        current_hour =  int(now / 3600) * 3600

        data = [random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700)]
        timestamps = self._populate_time_stamps(current_hour, len(data))
        # remove  1 and 2 hours ago data
        del data[1:3]
        del timestamps[1:3]

        aqi_type = random_string()
        # ToDo: optimize. Eliminate need _populate_time_stamps call (above)?
        records = []
        i = 0
        for concentration in data:
            records.append((timestamps[i], concentration))
            i += 1

        SUT = user.aqitype.NowCast(self.mock_logger, 0, None, None)

        start_vec, stop_vec, aqi_vec = SUT.calculate(aqi_type, iter(records))

        self.assertEqual(start_vec, [timestamps[0]])
        self.assertEqual(stop_vec, [timestamps[0] + 3600])
        self.assertEqual(aqi_vec, [None])

    def test_missing_middle_data(self):
        now = time.time()
        current_hour =  int(now / 3600) * 3600

        data = [149.5, 149.9, 238.6, None, None, None, None, None, 763.8, 744.6, 734.0, 711.8]
        timestamps = self._populate_time_stamps(current_hour, len(data))
        i = len(data) - 1
        while i >= 0 :
            if data[i] is None:
                del data[i]
                del timestamps[i]
            i -= 1

        aqi_type = 'pm2_5'
        # ToDo: optimize. Eliminate need _populate_time_stamps call (above)?
        records = []
        i = 0
        for concentration in data:
            records.append((timestamps[i], concentration))
            i += 1

        sub_calculator = user.aqitype.EPAAQI(self.mock_logger, 0, None, None)
        SUT = user.aqitype.NowCast(self.mock_logger, 0, sub_calculator, None)

        start_vec, stop_vec, aqi_vec = SUT.calculate(aqi_type, iter(records))

        self.assertEqual(start_vec, [timestamps[0]])
        self.assertEqual(stop_vec, [timestamps[0] + 3600])
        self.assertEqual(aqi_vec, [240])

    def test_beginning_none_data(self):
        now = time.time()
        current_hour =  int(now / 3600) * 3600

        data = [None,
                None,
                random.uniform(0, 700),
                random.uniform(0, 700),
                random.uniform(0, 700)]
        timestamps = self._populate_time_stamps(current_hour, len(data))

        aqi_type = random_string()
        # ToDo: optimize. Eliminate need _populate_time_stamps call (above)?
        records = []
        i = 0
        for concentration in data:
            records.append((timestamps[i], concentration))
            i += 1

        SUT = user.aqitype.NowCast(self.mock_logger, 0, None, None)

        start_vec, stop_vec, aqi_vec = SUT.calculate(aqi_type, iter(records))

        self.assertEqual(start_vec, [timestamps[0]])
        self.assertEqual(stop_vec, [timestamps[0] + 3600])
        self.assertEqual(aqi_vec, [None])

    def test_middle_none_data(self):
        now = time.time()
        current_hour =  int(now / 3600) * 3600

        data = [149.5, 149.9, 238.6, None, None, None, None, None, 763.8, 744.6, 734.0, 711.8]
        timestamps  = self._populate_time_stamps(current_hour, len(data))

        aqi_type = 'pm2_5'
        # ToDo: optimize. Eliminate need _populate_time_stamps call (above)?
        records = []
        i = 0
        for concentration in data:
            records.append((timestamps[i], concentration))
            i += 1

        sub_calculator = user.aqitype.EPAAQI(self.mock_logger, 0, None, None)
        SUT = user.aqitype.NowCast(self.mock_logger, 0, sub_calculator, None)

        start_vec, stop_vec, aqi_vec = SUT.calculate(aqi_type, iter(records))

        self.assertEqual(start_vec, [timestamps[0]])
        self.assertEqual(stop_vec, [timestamps[0] + 3600])
        self.assertEqual(aqi_vec, [240])

    def test_calculate_concentration(self):
        now = time.time()
        current_hour =  int(now / 3600) * 3600

        data = [46.3, 27.4, 59.8, 129.2, 130.6, 215.4, 143.2, 93.7, 101.8, 49.3, 80.2, 123.3]
        timestamps = self._populate_time_stamps(current_hour, len(data))

        aqi_type = 'pm2_5'
        # ToDo: optimize. Eliminate need _populate_time_stamps call (above)?
        records = []
        i = 0
        for concentration in data:
            records.append((timestamps[i], concentration))
            i += 1

        sub_calculator = user.aqitype.EPAAQI(self.mock_logger, 0, None, None)
        SUT = user.aqitype.NowCast(self.mock_logger, 0, sub_calculator, None)

        start_vec, stop_vec, aqi_vec = SUT.calculate(aqi_type, iter(records))

        self.assertEqual(start_vec, [timestamps[0]])
        self.assertEqual(stop_vec, [timestamps[0] + 3600])
        self.assertEqual(aqi_vec, [149])

if __name__ == '__main__':
    unittest.main(exit=False)
