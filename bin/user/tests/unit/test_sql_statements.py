#
#    Copyright (c) 2025 Rich Bell <bellrichm@gmail.com>
#
#    See the file LICENSE.txt for your full rights.
#

# pylint: disable=wrong-import-order
# pylint: disable=missing-docstring
# pylint: disable=invalid-name

import unittest
import mock

import configobj
import os
import random
import string
import sys
import time

import weeutil.weeutil

import user.aqitype

#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# pylint: disable=import-error, wrong-import-position
import utils.database
from utils import data
# pylint: enable=import-error, wrong-import-position


archive_intervals_in_day = 24 * 60 / utils.database.ARCHIVE_INTERVAL_MINUTES

def calculate_interval_average(full_data, interval_size):
    averages = []
    for subgroup in [full_data[i:i + interval_size] for i in range(0, len(full_data), interval_size)]:
        valid_values = [x for x in subgroup if x is not None]
        averages.append(sum(valid_values)/len(valid_values))

    return averages

def random_string(length=32):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(length)]) # pylint: disable=unused-variable

def mock_calculate_effect(*_args):
    return random.randint(1, 100)

def setup_config(calculated_field, input_field, algorithm, aqi_type):
    config_dict = {
        calculated_field: {
            'input': input_field,
            'algorithm': algorithm,
            'type': aqi_type,
        }
    }
    return config_dict

class TestSQL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.algorithm = 'EPAAQI'
        cls.aqi_type = 'pm2_5'
        cls.input_field = utils.database.PM2_5_INPUT_FIELD

        cls.db_manager = utils.database.get_db_manager(cls.input_field)

        # Create a backup of the database used in these tests.
        # This could be useful if there is a problem in the tests.
        utils.database.backup(cls.db_manager, 'bin/user/tests/utils/test_epa_calculate.sdb')

    @classmethod
    def tearDownClass(cls):
        cls.db_manager.close()
        cls.db_manager = None

    def setUp(self):
        self.mock_logger = mock.Mock(spec=user.aqitype.Logger)

        self.calculated_field = random_string()

        self.unit_group = [random_string(), random_string()]

        config_dict = setup_config(self.calculated_field,
                                   TestSQL.input_field,
                                   TestSQL.algorithm,
                                   TestSQL.aqi_type)
        self.config = configobj.ConfigObj(config_dict)

    def test_get_concentration_data_nowcast(self):
        SUT = user.aqitype.SQLExecutor(self.mock_logger)

        stop = min(weeutil.weeutil.startOfInterval(time.time(), 3600), utils.database.timespan.stop)

        records_iter = SUT.get_concentration_data_nowcast(self.db_manager, TestSQL.input_field, stop , utils.database.timespan.start - 43200)
        records = list(records_iter)
        timestamps, concentrations, _start_time = zip(*records)

        self.assertEqual(len(records), 36)
        # Get every 12th timestamp. These are the hour timestamps
        # Only want the last 12 hours of the previous day, 20250220
        self.assertEqual(list(timestamps),
                         list(reversed(data.db_20250221_timestamps[11:len(data.db_20250221_timestamps)-12:12])) + \
                         list(reversed((data.db_20250220_timestamps[143::12]))))
        # Compute the hourly average of the pm2_5 data
        # Only want the last 12 hours of the previous day, 20250220
        self.assertAlmostEqual(list(concentrations),
                         list(reversed(calculate_interval_average(data.db_20250221_pm2_5_values, 12))) + \
                         list(reversed(calculate_interval_average(data.db_20250220_pm2_5_values[144:], 12))))

    def test_get_concentration_data(self):
        SUT = user.aqitype.SQLExecutor(self.mock_logger)

        #timespan = (1740114000, 1740200400)
        records_iter = SUT.get_concentration_data(TestSQL.input_field, utils.database.timespan, TestSQL.db_manager)

        i = 0
        for record in records_iter:
            self.assertEqual(record,
                             (utils.data.db_20250221_timestamps[i],
                              utils.database.US_UNITS,
                              utils.database.ARCHIVE_INTERVAL_MINUTES,
                              utils.data.db_20250221_pm2_5_values[i]))
            i += 1

    def test_get_aggregate_avg_data(self):
        SUT = user.aqitype.SQLExecutor(self.mock_logger)

        query_type, records_iter = SUT.get_aggregate_concentation_data(TestSQL.input_field,
                                                                        utils.database.timespan,
                                                                        'avg',
                                                                        TestSQL.db_manager)

        self.assertEqual(query_type, 'aggregate')
        i = 0
        for record in records_iter:
            self.assertEqual(record, (utils.data.db_20250221_pm2_5_values[i],))
            i += 1

    def test_get_aggregate_min_data(self):
        SUT = user.aqitype.SQLExecutor(self.mock_logger)

        query_type, records_iter = SUT.get_aggregate_concentation_data(TestSQL.input_field,
                                                                        utils.database.timespan,
                                                                        'min',
                                                                        TestSQL.db_manager)

        self.assertEqual(query_type, 'basic')
        concentration = list(records_iter)[0][0]
        self.assertEqual(concentration, min(data.db_20250221_pm2_5_values))

    def test_get_aggregate_max_data(self):
        SUT = user.aqitype.SQLExecutor(self.mock_logger)

        query_type, records_iter = SUT.get_aggregate_concentation_data(TestSQL.input_field,
                                                                        utils.database.timespan,
                                                                        'max',
                                                                        TestSQL.db_manager)

        self.assertEqual(query_type, 'basic')
        concentration = list(records_iter)[0][0]
        self.assertEqual(concentration, max(data.db_20250221_pm2_5_values))

if __name__ == '__main__':
    #test_suite = unittest.TestSuite()
    #test_suite.addTest(TestSQL('test_get_concentration_data_nowcast'))
    #unittest.TextTestRunner().run(test_suite)

    unittest.main(exit=False)
