#    Copyright (c) 2023 Rich Bell <bellrichm@gmail.com>
#    See the file LICENSE.txt for your full rights.

# pylint: disable=missing-docstring

import time
import unittest

import mock

import weewx
import weeutil

import user.aqitype

class EPAAQITests(unittest.TestCase):
    def _populate_time_stamps(self, current_hour, count):
        time_stamps = []
        index = 0
        while index < count:
            time_stamps.append(current_hour - (count - index - 1) * 3600)
            index += 1

        return time_stamps

    def test_calculate_concentration(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval)as mock_start_of_imterval:
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with mock.patch('weewx.xtypes.ArchiveTable', spec=weewx.xtypes.ArchiveTable) as mock_xtype:
                    now = time.time()
                    current_hour =  int(now / 3600) * 3600
                    mock_start_of_imterval.return_value = current_hour

                    data = [[123.3, 80.2, 49.3, 101.8, 93.7, 143.2, 215.4, 130.6, 129.2, 59.8, 27.4, 46.3]]
                    start_vec = None
                    stop_vec = [self._populate_time_stamps(current_hour, len(data[0]))]
                    mock_xtype.return_value.get_series.return_value = start_vec, stop_vec, data

                    calculator = user.aqitype.NOWCAST(mock_logger, None, None)

                    concentration = calculator.calculate_concentration(None, current_hour, 'pm2_5')
                    self.assertEqual(concentration, 54.8)

if __name__ == '__main__':
    unittest.main(exit=False)
