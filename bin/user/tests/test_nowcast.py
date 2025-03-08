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
    min_value = values[0]
    max_value = values[0]
    for value in values:
        if value is not None:
            if value < min_value:
                min_value = value
            elif value > max_value:
                max_value = value
    return min_value, max_value

class NowCastTests(unittest.TestCase):
    def _populate_time_stamps(self, current_hour, count):
        time_stamps = []
        index = 0
        while index < count:
            time_stamps.append(current_hour - (index - 1) * 3600)
            index += 1

        return time_stamps

    def test_calculate_valid_inputs(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        mock_db_manager = mock.Mock()
        mock_calculator = mock.Mock()
        aqi = random.randint(1, 400)
        mock_calculator.calculate.return_value = aqi

        calculator = user.aqitype.NOWCAST(mock_logger, 0, mock_calculator, None)

        records_min_max = (random.randint(1, 10), random.randint(11, 20))
        records = [[random.randint(1, 100), random.random()]]

        with mock.patch.object(user.aqitype.NOWCAST, 'calculate_concentration', return_value=random.random()):
            ret_value = calculator.calculate(mock_db_manager, random_string(), (time.time(), records_min_max, records))

            self.assertEqual(ret_value, aqi)

    def test_incomplete_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with self.assertRaises(weewx.CannotCalculate):
                    data = [random.uniform(0, 700)]
                    data.reverse()
                    timestamps = self._populate_time_stamps(current_hour, len(data))

                    calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

                    calculator.calculate_concentration(now, min(data), max(data), timestamps, data)

    def test_old_minimum_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with self.assertRaises(weewx.CannotCalculate):
                    data = [random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700)]
                    timestamps = self._populate_time_stamps(current_hour, len(data))
                    # remove  1 and 2 hours ago data
                    del data[1:3]
                    del timestamps[1:3]

                    data.reverse()

                    calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

                    calculator.calculate_concentration(now, min(data), max(data), timestamps, data)

    def test_old_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with self.assertRaises(weewx.CannotCalculate):
                    data = [random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700),
                                random.uniform(0, 700), random.uniform(0, 700)]
                    data.reverse()
                    timestamps = self._populate_time_stamps(current_hour, len(data))
                    # remove  1 and 2 hours ago data
                    del data[:2]
                    del timestamps[:2]

                    calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

                    calculator.calculate_concentration(now, min(data), max(data), timestamps, data)

    def test_missing_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                data = [711.8, 734.0, 744.6, 763.8, None, None, None, None, None, 238.6, 149.9, 149.5]
                timestamps = self._populate_time_stamps(current_hour, len(data))
                data.reverse()
                i = len(data) - 1
                while i >= 0 :
                    if data[i] is None:
                        del data[i]
                        del timestamps[i]
                    i -= 1

                calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

                concentration = calculator.calculate_concentration(now, min(data), max(data), timestamps, data)
                self.assertEqual(concentration, 164.7)

    def test_none_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                data = [711.8, 734.0, 744.6, 763.8, None, None, None, None, None, 238.6, 149.9, 149.5]
                min_value, max_value = min_max(data)
                timestamps  = self._populate_time_stamps(current_hour, len(data))

                data.reverse()

                calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)
                concentration = calculator.calculate_concentration(now, min_value, max_value, timestamps, data)
                self.assertEqual(concentration, 164.7)

    def test_calculate_concentration(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        now = time.time()
        current_hour =  int(now / 3600) * 3600

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval, return_value=current_hour):
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                data = [123.3, 80.2, 49.3, 101.8, 93.7, 143.2, 215.4, 130.6, 129.2, 59.8, 27.4, 46.3]
                data.reverse()
                timestamps = self._populate_time_stamps(current_hour, len(data))

                calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

                concentration = calculator.calculate_concentration(now, min(data), max(data), timestamps, data)
                self.assertEqual(concentration, 54.8)

    @unittest.skip("placeholder")
    def test_calculate_series(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

        result = calculator.calculate_series('foo', [])

        print(result)

        print("done")

if __name__ == '__main__':
    unittest.main(exit=False)
