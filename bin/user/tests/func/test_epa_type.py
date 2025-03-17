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

import user.aqitype

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# pylint: disable=import-error, wrong-import-position
import utils.database
# pylint: enable=import-error, wrong-import-position

def random_string(length=32):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(length)]) # pylint: disable=unused-variable

def setup_config(calculated_field, input_field, algorithm, aqi_type):
    config_dict = {
        calculated_field: {
            'input': input_field,
            'algorithm': algorithm,
            'type': aqi_type,
        }
    }
    return config_dict

class TestEPAGetScalar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input_field = utils.database.PM2_5_INPUT_FIELD
        cls.db_manager = utils.database.get_db_manager(cls.input_field)

        # Create a backup of the database used in these tests.
        # This could be useful if there is a problem in the tests.
        utils.database.backup(cls.db_manager, 'bin/user/tests/utils/test_nowcast_calculate.sdb')

    @classmethod
    def tearDownClass(cls):
        cls.db_manager.close()
        cls.db_manager = None

    def setUp(self):
        self.mock_logger = mock.Mock(spec=user.aqitype.Logger)

    def test_get_scalar_valid_inputs(self):
        algorithm = 'EPAAQI'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = random_string()

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        SUT = user.aqitype.AQIType(self.mock_logger, user.aqitype.SQLExecutor(self.mock_logger), config)

        input_concentration = 10
        calculated_aqi = 53

        record = {
            'usUnits': utils.database.US_UNITS,
            'interval': utils.database.ARCHIVE_INTERVAL_MINUTES,
            'dateTime': random.randint(1, 1000),
            input_field: input_concentration,
        }

        value_tuple = SUT.get_scalar(calculated_field, record)

        self.assertEqual(value_tuple[0], calculated_aqi)
        self.assertEqual(value_tuple[1], None)
        self.assertEqual(value_tuple[2], None)

class TestEPAGetSeries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input_field = utils.database.PM2_5_INPUT_FIELD
        cls.db_manager = utils.database.get_db_manager(cls.input_field)

        # Create a backup of the database used in these tests.
        # This could be useful if there is a problem in the tests.
        utils.database.backup(cls.db_manager, 'bin/user/tests/utils/test_nowcast_calculate.sdb')

    @classmethod
    def tearDownClass(cls):
        cls.db_manager.close()
        cls.db_manager = None

    def setUp(self):
        self.mock_logger = mock.Mock(spec=user.aqitype.Logger)

    def test_get_series_valid_inputs(self):
        algorithm = 'EPAAQI'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = utils.database.PM2_5_INPUT_FIELD

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        SUT = user.aqitype.AQIType(self.mock_logger, user.aqitype.SQLExecutor(self.mock_logger), config)

        start_vec_t, stop_vec_t, data_vec_t  = SUT.get_series(calculated_field, utils.database.timespan, TestEPAGetSeries.db_manager)

        expected_aqi = [
            6, 5, 6, 12, 8, 10, 11, 15, 14, 10, 9, 11, 4, 8, 8, 7, 8, 5, 6, 8, 7, 9, 9, 5,
            5, 5, 10, 7, 5, 7, 10, 8, 6, 6, 8, 9, 9, 5, 9, 12, 7, 8, 9, 10, 7, 10, 8, 6,
            8, 7, 7, 7, 6, 6, 7, 7, 6, 8, 8, 7, 5, 6, 7, 9, 8, 8, 7, 8, 7, 5, 6, 5,
            8, 11, 8, 8, 11, 7, 9, 7, 6, 7, 6, 7, 6, 8, 8, 7, 10, 7, 10, 10, 9, 7, 5, 6,
            13, 6, 9, 9, 6, 11, 10, 8, 6, 10, 9, 8, 10, 8,6, 6, 7, 9, 6, 10, 5, 9, 6, 7,
            10, 9, 10, 9, 6, 6, 8, 8, 8, 12, 8, 8, 8, 11, 10, 7, 5, 8, 10, 8, 5, 7, 8, 7,
            8, 9, 8, 10, 12, 10, 7, 12, 9, 9, 8, 12, 9, 8, 8, 6, 9, 9, 6, 8, 7, 8, 13, 10,
            14, 11, 6, 8, 8, 4, 5, 10, 7, 8, 6, 8, 10, 10, 6, 7, 5, 6, 6, 12, 7, 7, 7, 9,
            8, 7, 6, 5, 8, 7, 10, 8, 6, 8, 12, 7, 4, 6, 8, 5, 9, 9, 7, 4, 9, 6, 7, 9,
            7, 12, 9, 9, 5, 8, 8, 6, 9, 8, 6, 5, 6, 5, 6, 8, 7, 7, 6, 5, 4, 5, 6, 4,
            7, 9, 10, 9, 7, 5, 8, 5, 7, 7, 8, 9, 9, 7, 10, 6, 7, 5, 6, 6, 10, 8, 8, 13,
            7, 6, 7, 6, 5, 8, 6, 8, 7, 10, 10, 9, 12, 9, 7, 7, 7, 10, 8, 10, 9, 10, 11, 9,
        ]

        self.assertEqual(start_vec_t,
                        ([utils.data.db_20250221_timestamps[0] - utils.database.ARCHIVE_INTERVAL_SECONDS] +
                          utils.data.db_20250221_timestamps[0:-1],
                        'unix_epoch',
                        'group_time'))
        self.assertEqual(stop_vec_t, (utils.data.db_20250221_timestamps, 'unix_epoch', 'group_time'))

        self.assertEqual(data_vec_t, (expected_aqi, None, None))

    def test_get_aggregated_series_valid_inputs(self):
        algorithm = 'EPAAQI'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = utils.database.PM2_5_INPUT_FIELD

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        SUT = user.aqitype.AQIType(self.mock_logger, user.aqitype.SQLExecutor(self.mock_logger), config)

        value_tuple  = SUT.get_series(calculated_field,
                                    utils.database.timespan,
                                    TestEPAGetSeries.db_manager,
                                    'min',
                                    3600)

        expected_aqi = ([5, 4, 5, 5, 6, 5, 6, 5, 6, 5, 6, 5, 7, 6, 4, 5, 5, 4, 5, 4, 5, 5, 5, 7], None, None)

        self.assertEqual(value_tuple[0], ([1740114000] + utils.data.db_20250221_timestamps[11:-1:12], 'unix_epoch', 'group_time'))
        self.assertEqual(value_tuple[1], (utils.data.db_20250221_timestamps[11::12], 'unix_epoch', 'group_time'))
        self.assertEqual(value_tuple[2], expected_aqi)

class TestEPAGetAggregate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input_field = utils.database.PM2_5_INPUT_FIELD
        cls.db_manager = utils.database.get_db_manager(cls.input_field)

        # Create a backup of the database used in these tests.
        # This could be useful if there is a problem in the tests.
        utils.database.backup(cls.db_manager, 'bin/user/tests/utils/test_nowcast_calculate.sdb')

    @classmethod
    def tearDownClass(cls):
        cls.db_manager.close()
        cls.db_manager = None

    def setUp(self):
        self.mock_logger = mock.Mock(spec=user.aqitype.Logger)

    def test_get_aggregation_avg_valid_inputs(self):
        algorithm = 'EPAAQI'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = utils.database.PM2_5_INPUT_FIELD

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        SUT = user.aqitype.AQIType(self.mock_logger, user.aqitype.SQLExecutor(self.mock_logger), config)

        value_tuple  = SUT.get_aggregate(calculated_field, utils.database.timespan, 'min', TestEPAGetAggregate.db_manager)

        expected_aqi = 4

        self.assertEqual(value_tuple[0], expected_aqi)
        self.assertEqual(value_tuple[1], None)
        self.assertEqual(value_tuple[2], None)

if __name__ == '__main__':
    #test_suite = unittest.TestSuite()
    #test_suite.addTest(TestNowCastDevelopment('test_get_series_prototype02'))
    #unittest.TextTestRunner().run(test_suite)

    unittest.main(exit=False)
