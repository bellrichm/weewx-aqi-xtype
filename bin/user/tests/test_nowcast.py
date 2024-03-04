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
            time_stamps.append(current_hour - (count - index - 1) * 3600)
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
                with mock.patch('weewx.xtypes.ArchiveTable', spec=weewx.xtypes.ArchiveTable) as mock_xtype:
                    with self.assertRaises(weewx.CannotCalculate):
                        now = time.time()
                        current_hour =  int(now / 3600) * 3600
                        mock_start_of_interval.return_value = current_hour

                        data = [[random.uniform(0, 700)]]
                        start_vec = None
                        stop_vec = [self._populate_time_stamps(current_hour, len(data[0]))]

                        mock_xtype.return_value.get_series.return_value = start_vec, stop_vec, data

                        calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

                        calculator.calculate_concentration(None, current_hour)

    def test_old_minimum_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval)as mock_start_of_interval:
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with mock.patch('weewx.xtypes.ArchiveTable', spec=weewx.xtypes.ArchiveTable) as mock_xtype:
                    with self.assertRaises(weewx.CannotCalculate):
                        now = time.time()
                        current_hour =  int(now / 3600) * 3600
                        mock_start_of_interval.return_value = current_hour

                        data = [[random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700)]]
                        start_vec = None
                        stop_vec = [self._populate_time_stamps(current_hour, len(data[0]))]
                        # remove  1 and 2 hours ago data
                        del data[0][1:3]
                        del stop_vec[0][1:3]

                        mock_xtype.return_value.get_series.return_value = start_vec, stop_vec, data

                        calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

                        calculator.calculate_concentration(None, current_hour)

    def test_old_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval)as mock_start_of_interval:
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with mock.patch('weewx.xtypes.ArchiveTable', spec=weewx.xtypes.ArchiveTable) as mock_xtype:
                    with self.assertRaises(weewx.CannotCalculate):
                        now = time.time()
                        current_hour =  int(now / 3600) * 3600
                        mock_start_of_interval.return_value = current_hour

                        data = [[random.uniform(0, 700), random.uniform(0, 700), random.uniform(0, 700),
                                 random.uniform(0, 700), random.uniform(0, 700)]]
                        start_vec = None
                        stop_vec = [self._populate_time_stamps(current_hour, len(data[0]))]
                        # remove  1 and 2 hours ago data
                        del data[0][len(stop_vec[0]) - 2:]
                        del stop_vec[0][len(stop_vec[0]) - 2:]

                        mock_xtype.return_value.get_series.return_value = start_vec, stop_vec, data

                        calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

                        calculator.calculate_concentration(None, current_hour)

    def test_missing_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval)as mock_start_of_interval:
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with mock.patch('weewx.xtypes.ArchiveTable', spec=weewx.xtypes.ArchiveTable) as mock_xtype:
                    now = time.time()
                    current_hour =  int(now / 3600) * 3600
                    mock_start_of_interval.return_value = current_hour

                    data = [[711.8, 734.0, 744.6, 763.8, None, None, None, None, None, 238.6, 149.9, 149.5]]
                    start_vec = None
                    stop_vec = [self._populate_time_stamps(current_hour, len(data[0]))]
                    i = len(data[0]) - 1
                    while i >= 0 :
                        if data[0][i] is None:
                            del data[0][i]
                            del stop_vec[0][i]
                        i -= 1

                    mock_xtype.return_value.get_series.return_value = start_vec, stop_vec, data

                    calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

                    concentration = calculator.calculate_concentration(None, current_hour)
                    self.assertEqual(concentration, 164.7)

    def test_none_data(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval)as mock_start_of_interval:
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with mock.patch('weewx.xtypes.ArchiveTable', spec=weewx.xtypes.ArchiveTable) as mock_xtype:
                    now = time.time()
                    current_hour =  int(now / 3600) * 3600
                    mock_start_of_interval.return_value = current_hour

                    data = [[711.8, 734.0, 744.6, 763.8, None, None, None, None, None, 238.6, 149.9, 149.5]]
                    start_vec = None
                    stop_vec = [self._populate_time_stamps(current_hour, len(data[0]))]

                    mock_xtype.return_value.get_series.return_value = start_vec, stop_vec, data

                    calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)
                    concentration = calculator.calculate_concentration(None, current_hour)
                    self.assertEqual(concentration, 164.7)

    def test_calculate_concentration(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval)as mock_start_of_interval:
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with mock.patch('weewx.xtypes.ArchiveTable', spec=weewx.xtypes.ArchiveTable) as mock_xtype:
                    now = time.time()
                    current_hour =  int(now / 3600) * 3600
                    mock_start_of_interval.return_value = current_hour

                    data = [[123.3, 80.2, 49.3, 101.8, 93.7, 143.2, 215.4, 130.6, 129.2, 59.8, 27.4, 46.3]]
                    start_vec = None
                    stop_vec = [self._populate_time_stamps(current_hour, len(data[0]))]

                    mock_xtype.return_value.get_series.return_value = start_vec, stop_vec, data

                    calculator = user.aqitype.NOWCAST(mock_logger, 0, None, None)

                    concentration = calculator.calculate_concentration(None, current_hour)
                    self.assertEqual(concentration, 54.8)

if __name__ == '__main__':
    unittest.main(exit=False)
