#    Copyright (c) 2023-2025 Rich Bell <bellrichm@gmail.com>
#    See the file LICENSE.txt for your full rights.

# pylint: disable=missing-docstring

import random
import string
import time
import unittest

import mock

import weewx
import weeutil

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

def populate_time_stamps(current_hour, count):
    time_stamps = []
    index = 0
    while index < count:
        time_stamps.append(current_hour - (index - 1) * 3600)
        index += 1
    return time_stamps

class TestNowCastCalculate(unittest.TestCase):
    def test_invalid_inputs_single(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with mock.patch.object(user.aqitype.NowCast, 'calculate_concentration',side_effect=weewx.CannotCalculate):
                    data = [random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700)]
                    timestamps = populate_time_stamps(current_hour, len(data))
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

                    calculator = user.aqitype.NowCast(mock_logger, 0, None, None)

                    stats, start_vec, stop_vec, aqi_vec = calculator.calculate(aqi_type, iter(records))

                    vec_len = len(start_vec)
                    self.assertFalse(stats.not_null)
                    self.assertEqual(stats.count, 0)
                    self.assertEqual(stats.sum, 0)
                    self.assertIsNone(stats.first)
                    self.assertIsNone(stats.last)
                    self.assertIsNone(stats.firsttime)
                    self.assertIsNone(stats.lasttime)
                    self.assertIsNone(stats.min)
                    self.assertIsNone(stats.max)
                    self.assertIsNone(stats.mintime)
                    self.assertIsNone(stats.maxtime)
                    self.assertEqual(start_vec, list(reversed(timestamps[0:vec_len])))
                    self.assertEqual(stop_vec, list(reversed([x+3600 for x in timestamps[0:vec_len]])))
                    self.assertEqual(aqi_vec, [None])

    def test_valid_inputs_single(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with mock.patch.object(user.aqitype.NowCast, 'calculate_concentration'):
                    aqi_values = [random.randint(0, 500)]
                    data = [random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700),
                            random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700),
                            random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700),
                            random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700)]
                    timestamps = populate_time_stamps(current_hour, len(data))
                    i = len(data) - 1
                    while i >= 0 :
                        if data[i] is None:
                            del data[i]
                            del timestamps[i]
                        i -= 1

                    aqi_type = random_string()
                    # ToDo: optimize. Eliminate need _populate_time_stamps call (above)?
                    records = []
                    i = 0
                    for concentration in data:
                        records.append((timestamps[i], concentration))
                        i += 1

                    sub_calculator= mock.Mock()
                    sub_calculator.calculate.side_effect = aqi_values
                    calculator = user.aqitype.NowCast(mock_logger, 0, sub_calculator, None)

                    stats, start_vec, stop_vec, aqi_vec = calculator.calculate(aqi_type, iter(records))

                    vec_len = len(start_vec)
                    self.assertTrue(stats.not_null)
                    self.assertEqual(stats.count, 1)
                    self.assertEqual(stats.sum, sum(aqi_values))
                    self.assertEqual(stats.first, aqi_values[-1])
                    self.assertEqual(stats.last, aqi_values[0])
                    self.assertEqual(stats.firsttime, timestamps[vec_len-1])
                    self.assertEqual(stats.lasttime, timestamps[0])
                    self.assertEqual(stats.min, min(aqi_values))
                    self.assertEqual(stats.max, max(aqi_values))
                    self.assertEqual(stats.mintime, timestamps[aqi_values.index(stats.min)])
                    self.assertEqual(stats.maxtime, timestamps[aqi_values.index(stats.max)])
                    self.assertEqual(start_vec, list(reversed(timestamps[0:vec_len])))
                    self.assertEqual(stop_vec, list(reversed([x+3600 for x in timestamps[0:vec_len]])))
                    self.assertEqual(aqi_vec, list(reversed(aqi_values)))

    def test_invalid_inputs_multi(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with mock.patch.object(user.aqitype.NowCast, 'calculate_concentration', side_effect=['foo', 'bar', weewx.CannotCalculate]):

                    aqi_values = [random.randint(0, 500), random.randint(0,500)]
                    data = [random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700),
                            None, None, random.uniform(0, 700),
                            random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700),
                            random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700),
                            random.uniform(0, 700), random.uniform(0, 700)]
                    timestamps = populate_time_stamps(current_hour, len(data))

                    aqi_type = random_string()
                    # ToDo: optimize. Eliminate need _populate_time_stamps call (above)?
                    records = []
                    i = 0
                    for concentration in data:
                        records.append((timestamps[i], concentration))
                        i += 1

                    sub_calculator= mock.Mock()
                    sub_calculator.calculate.side_effect = aqi_values
                    calculator = user.aqitype.NowCast(mock_logger, 0, sub_calculator, None)

                    stats, start_vec, stop_vec, aqi_vec = calculator.calculate(aqi_type, iter(records))

                    vec_len = len(start_vec)
                    self.assertTrue(stats.not_null)
                    self.assertEqual(stats.count, 2)
                    self.assertEqual(stats.sum, sum(aqi_values))
                    self.assertEqual(stats.first, aqi_values[-1])
                    self.assertEqual(stats.last, aqi_values[0])
                    self.assertEqual(stats.firsttime, timestamps[vec_len-2])
                    self.assertEqual(stats.lasttime, timestamps[0])
                    self.assertEqual(stats.min, min(aqi_values))
                    self.assertEqual(stats.max, max(aqi_values))
                    self.assertEqual(stats.mintime, timestamps[aqi_values.index(stats.min)])
                    self.assertEqual(stats.maxtime, timestamps[aqi_values.index(stats.max)])
                    self.assertEqual(start_vec, list(reversed(timestamps[0:vec_len])))
                    self.assertEqual(stop_vec, list(reversed([x+3600 for x in timestamps[0:vec_len]])))
                    self.assertEqual(aqi_vec, [None] + list(reversed(aqi_values)))

    def test_valid_inputs_multi(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with mock.patch.object(user.aqitype.NowCast, 'calculate_concentration'):
                    aqi_values = [random.randint(0, 500), random.randint(0,500)]
                    data = [random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700),
                            random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700),
                            random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700),
                            random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700),
                            random.uniform(0, 700)]
                    timestamps = populate_time_stamps(current_hour, len(data))

                    aqi_type = random_string()
                    # ToDo: optimize. Eliminate need _populate_time_stamps call (above)?
                    records = []
                    i = 0
                    for concentration in data:
                        records.append((timestamps[i], concentration))
                        i += 1

                    sub_calculator= mock.Mock()
                    sub_calculator.calculate.side_effect = aqi_values
                    calculator = user.aqitype.NowCast(mock_logger, 0, sub_calculator, None)

                    stats, start_vec, stop_vec, aqi_vec = calculator.calculate(aqi_type, iter(records))

                    vec_len = len(start_vec)
                    self.assertTrue(stats.not_null)
                    self.assertEqual(stats.count, 2)
                    self.assertEqual(stats.sum, sum(aqi_values))
                    self.assertEqual(stats.first, aqi_values[-1])
                    self.assertEqual(stats.last, aqi_values[0])
                    self.assertEqual(stats.firsttime, timestamps[vec_len-1])
                    self.assertEqual(stats.lasttime, timestamps[0])
                    self.assertEqual(stats.min, min(aqi_values))
                    self.assertEqual(stats.max, max(aqi_values))
                    self.assertEqual(stats.mintime, timestamps[aqi_values.index(stats.min)])
                    self.assertEqual(stats.maxtime, timestamps[aqi_values.index(stats.max)])
                    self.assertEqual(start_vec, list(reversed(timestamps[0:vec_len])))
                    self.assertEqual(stop_vec, list(reversed([x+3600 for x in timestamps[0:vec_len]])))
                    self.assertEqual(aqi_vec, list(reversed(aqi_values)))

class TestNowCastCalculateConcentration(unittest.TestCase):
    def test_incomplete_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with self.assertRaises(weewx.CannotCalculate):
                    data = [random.uniform(0, 700)]
                    timestamps = populate_time_stamps(current_hour, len(data))

                    calculator = user.aqitype.NowCast(mock_logger, 0, None, None)

                    calculator.calculate_concentration(current_hour, min(data), max(data), timestamps, data)

    def test_beginning_missing_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with self.assertRaises(weewx.CannotCalculate):
                    data = [random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700)]
                    timestamps = populate_time_stamps(current_hour, len(data))
                    # remove  1 and 2 hours ago data
                    del data[1:3]
                    del timestamps[1:3]

                    calculator = user.aqitype.NowCast(mock_logger, 0, None, None)

                    calculator.calculate_concentration(current_hour, min(data), max(data), timestamps, data)

    def test_missing_middle_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                data = [149.5, 149.9, 238.6, None, None, None, None, None, 763.8, 744.6, 734.0, 711.8]
                timestamps = populate_time_stamps(current_hour, len(data))
                i = len(data) - 1
                while i >= 0 :
                    if data[i] is None:
                        del data[i]
                        del timestamps[i]
                    i -= 1

                calculator = user.aqitype.NowCast(mock_logger, 0, None, None)

                concentration = calculator.calculate_concentration(current_hour, min(data), max(data), timestamps, data)
                self.assertEqual(concentration, 164.7)

    def test_beginning_none_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with self.assertRaises(weewx.CannotCalculate):
                    data = [None,
                            None,
                            random.uniform(0, 700),
                            random.uniform(0, 700),
                            random.uniform(0, 700)]
                    min_value, max_value = min_max(data)
                    timestamps = populate_time_stamps(current_hour, len(data))

                    calculator = user.aqitype.NowCast(mock_logger, 0, None, None)

                    calculator.calculate_concentration(current_hour, min_value, max_value, timestamps, data)

    def test_middle_none_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                data = [149.5, 149.9, 238.6, None, None, None, None, None, 763.8, 744.6, 734.0, 711.8]
                min_value, max_value = min_max(data)
                timestamps  = populate_time_stamps(current_hour, len(data))

                calculator = user.aqitype.NowCast(mock_logger, 0, None, None)
                concentration = calculator.calculate_concentration(current_hour, min_value, max_value, timestamps, data)
                self.assertEqual(concentration, 164.7)

    def test_calculate_concentration(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                data = [46.3, 27.4, 59.8, 129.2, 130.6, 215.4, 143.2, 93.7, 101.8, 49.3, 80.2, 123.3]
                timestamps = populate_time_stamps(current_hour, len(data))

                calculator = user.aqitype.NowCast(mock_logger, 0, None, None)

                concentration = calculator.calculate_concentration(current_hour, min(data), max(data), timestamps, data)
                self.assertEqual(concentration, 54.8)

if __name__ == '__main__':
    unittest.main(exit=False)
