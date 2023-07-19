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

    def test_calculate_concentration(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        with mock.patch('weeutil.weeutil.startOfInterval', spec=weeutil.weeutil.startOfInterval)as mock_start_of_imterval:
            with mock.patch('weeutil.weeutil.TimeSpan', spec=weeutil.weeutil.TimeSpan):
                with mock.patch('weewx.xtypes.ArchiveTable', spec=weewx.xtypes.ArchiveTable) as mock_xtype:
                    now = time.time()
                    current_hour =  int(now / 3600) * 3600
                    mock_start_of_imterval.return_value = current_hour

                    start_vec = None
                    stop_vec = []
                    stop_vec.append([])
                    data = []
                    data.append([])
                    data[0].append(123.3)
                    data[0].append(80.2)
                    data[0].append(49.3)
                    data[0].append(101.8)
                    data[0].append(93.7)
                    data[0].append(143.2)
                    data[0].append(215.4)
                    data[0].append(130.6)
                    data[0].append(129.2)
                    data[0].append(59.8)
                    data[0].append(27.4)
                    data[0].append(46.3)

                    index = 0
                    data_count = len(data[0])
                    while index < data_count:
                        stop_vec[0].append(current_hour - (data_count - index - 1) * 3600)
                        index += 1

                    mock_xtype.return_value.get_series.return_value = start_vec, stop_vec, data

                    calculator = user.aqitype.NOWCAST(mock_logger, None, None)

                    concentration = calculator.calculate_concentration(None, current_hour, 'pm2_5')
                    self.assertEqual(concentration, 54.8)

if __name__ == '__main__':
    unittest.main(exit=False)
