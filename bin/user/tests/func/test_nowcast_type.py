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

class TestNowCastGetScalar(unittest.TestCase):
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
        algorithm = 'NowCast'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = utils.database.PM2_5_INPUT_FIELD

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        SUT = user.aqitype.AQIType(self.mock_logger, user.aqitype.SQLExecutor(self.mock_logger), config)

        record = {
            'usUnits': utils.database.US_UNITS,
            'interval': utils.database.ARCHIVE_INTERVAL_MINUTES,
            'dateTime': 1740168000,
            input_field: input_field,
        }

        value_tuple = SUT.get_scalar(calculated_field, record, TestNowCastGetScalar.db_manager)

        self.assertEqual(value_tuple[0], 8)
        self.assertEqual(value_tuple[1], None)
        self.assertEqual(value_tuple[2], None)

class TestNowCastGetSeries(unittest.TestCase):
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
        algorithm = 'NowCast'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = utils.database.PM2_5_INPUT_FIELD

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        SUT = user.aqitype.AQIType(self.mock_logger, user.aqitype.SQLExecutor(self.mock_logger), config)
        start_vec, stop_vec, aqi_vec = SUT.get_series(calculated_field, utils.database.timespan, TestNowCastGetSeries.db_manager)

        self.assertEqual(start_vec,
                         ([1740114000, 1740117600, 1740121200, 1740124800, 1740128400, 1740132000,
                           1740135600, 1740139200, 1740142800, 1740146400, 1740150000, 1740153600,
                           1740157200, 1740160800, 1740164400, 1740168000, 1740171600, 1740175200,
                           1740178800, 1740182400, 1740186000, 1740189600, 1740193200, 1740196800],
                          'unix_epoch', 'group_time'))
        self.assertEqual(stop_vec,
                         ([1740117600, 1740121200, 1740124800, 1740128400, 1740132000, 1740135600,
                           1740139200, 1740142800, 1740146400, 1740150000, 1740153600, 1740157200,
                           1740160800, 1740164400, 1740168000, 1740171600, 1740175200, 1740178800,
                           1740182400, 1740186000, 1740189600, 1740193200, 1740196800, 1740200400],
                          'unix_epoch', 'group_time'))                           
        self.assertEqual(aqi_vec,
                         ([9, 8, 7, 8, 7, 7,7, 7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 7, 7, 7, 7, 7, 7, 8],
                          None, None))

class TestNowCastGetAggregate(unittest.TestCase):
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


    def test_get_aggregate_type_not_null(self):
        algorithm = 'NowCast'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = utils.database.PM2_5_INPUT_FIELD

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        SUT = user.aqitype.AQIType(self.mock_logger, user.aqitype.SQLExecutor(self.mock_logger), config)

        aggregate_value = SUT.get_aggregate(calculated_field, utils.database.timespan, 'not_null', TestNowCastGetAggregate.db_manager)

        self.assertEqual(aggregate_value, (True, 'boolean', 'group_boolean'))

if __name__ == '__main__':
    #test_suite = unittest.TestSuite()
    #test_suite.addTest(TestNowCastDevelopment('test_get_series_prototype02'))
    #unittest.TextTestRunner().run(test_suite)

    unittest.main(exit=False)
