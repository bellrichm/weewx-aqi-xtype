#    Copyright (c) 2023-2024 Rich Bell <bellrichm@gmail.com>
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

class NowCastTests(unittest.TestCase):
    def _populate_time_stamps(self, current_hour, count):
        time_stamps = []
        index = 0
        while index < count:
            time_stamps.append(current_hour - (index - 1) * 3600)
            index += 1

        return time_stamps

    def test_invalid_time_stamp(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        with self.assertRaises(weewx.CannotCalculate):
            calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

            calculator.calculate(None, None, None, random_string())

    def test_incomplete_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval)as mock_start_of_interval:
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with self.assertRaises(weewx.CannotCalculate):
                    now = time.time()
                    current_hour =  int(now / 3600) * 3600
                    mock_start_of_interval.return_value = current_hour

                    data = [random.uniform(0, 700)]
                    data.reverse()
                    timestamps = self._populate_time_stamps(current_hour, len(data))

                    calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

                    calculator.calculate_concentration(current_hour, len(data), min(data), max(data), timestamps, data)

    def test_old_minimum_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval)as mock_start_of_interval:
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with self.assertRaises(weewx.CannotCalculate):
                    now = time.time()
                    current_hour =  int(now / 3600) * 3600
                    mock_start_of_interval.return_value = current_hour

                    data = [random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700)]
                    timestamps = self._populate_time_stamps(current_hour, len(data))
                    # remove  1 and 2 hours ago data
                    del data[1:3]
                    del timestamps[1:3]

                    data.reverse()

                    calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

                    calculator.calculate_concentration(current_hour, len(data), min(data), max(data), timestamps, data)

    def test_old_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval)as mock_start_of_interval:
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with self.assertRaises(weewx.CannotCalculate):
                    now = time.time()
                    current_hour =  int(now / 3600) * 3600
                    mock_start_of_interval.return_value = current_hour

                    data = [random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700),
                                random.uniform(0, 700), random.uniform(0, 700)]
                    data.reverse()
                    timestamps = self._populate_time_stamps(current_hour, len(data))
                    # remove  1 and 2 hours ago data
                    del data[:2]
                    del timestamps[:2]

                    calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

                    calculator.calculate_concentration(current_hour, len(data), min(data), max(data), timestamps, data)

    def test_missing_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval)as mock_start_of_interval:
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                now = time.time()
                current_hour =  int(now / 3600) * 3600
                mock_start_of_interval.return_value = current_hour

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

                concentration = calculator.calculate_concentration(current_hour, len(data), min(data), max(data), timestamps, data)
                self.assertEqual(concentration, 164.7)

    @unittest.skip("no longer valid - 'None' will never be in the data")
    def test_none_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval)as mock_start_of_interval:
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                now = time.time()
                current_hour =  int(now / 3600) * 3600
                mock_start_of_interval.return_value = current_hour

                data = [711.8, 734.0, 744.6, 763.8, None, None, None, None, None, 238.6, 149.9, 149.5]
                timestamps  = self._populate_time_stamps(current_hour, len(data))

                data.reverse()

                calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)
                concentration = calculator.calculate_concentration(current_hour, len(data), min(data), max(data), timestamps, data)
                self.assertEqual(concentration, 164.7)

    def test_calculate_concentration(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval)as mock_start_of_interval:
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                now = time.time()
                current_hour =  int(now / 3600) * 3600
                mock_start_of_interval.return_value = current_hour

                data = [123.3, 80.2, 49.3, 101.8, 93.7, 143.2, 215.4, 130.6, 129.2, 59.8, 27.4, 46.3]
                data.reverse()
                timestamps = self._populate_time_stamps(current_hour, len(data))

                calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

                concentration = calculator.calculate_concentration(current_hour, len(data), min(data), max(data), timestamps, data)
                self.assertEqual(concentration, 54.8)

if __name__ == '__main__':
    unittest.main(exit=False)
