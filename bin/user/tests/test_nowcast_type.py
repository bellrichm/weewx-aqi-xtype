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
import random
import string
import time

import user.aqitype

import utils.database

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

class TestGetScalarNowcast(unittest.TestCase):
    def test_get_scalar_valid_inputs(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        mock_db_manager = mock.Mock()

        calculator = user.aqitype.NOWCAST
        algorithm = 'NOWCAST'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = random_string()

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        aqi = random.randint(11, 100)
        with mock.patch.object(calculator, 'calculate', return_value=aqi):
            SUT = user.aqitype.AQIType(mock_logger, config)

            unit = random_string()
            unit_group = random_string()

            record = {
                'usUnits': utils.database.US_UNITS,
                'interval': utils.database.ARCHIVE_INTERVAL_MINUTES,
                'dateTime': time.time(),
                input_field: random.randint(0, 10),
            }

            data_stats = (random.randint(8, 12), random.random(), random.random())
            with mock.patch('weewx.units.getStandardUnitType', return_value=[unit, unit_group]):
                with mock.patch.object(user.aqitype.AQIType, 'get_concentration_data_stats', return_value=data_stats):
                    value_tuple = SUT.get_scalar(calculated_field, record, mock_db_manager)

                self.assertEqual(value_tuple[0], aqi)
                self.assertEqual(value_tuple[1], unit)
                self.assertEqual(value_tuple[2], unit_group)

class TestNowcastDevelopment(unittest.TestCase):
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

    def test_calculate_series_prototype(self):
        # ToDo: This 'test' will be used to develop series support for the Nowcast algorithm.
        #       Note, due to performance concerns, I am not sure the Nowcast algotithm will be supported.
        #
        #sub_calculator = user.aqitype.EPAAQI(self.mock_logger, random.randint(1, 100), None, None)
        #SUT = user.aqitype.NOWCAST(self.mock_logger, random.randint(1, 100), sub_calculator, TestNowcastDevelopment.input_field)

        algorithm = 'NOWCAST'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = utils.database.PM2_5_INPUT_FIELD

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        SUT = user.aqitype.AQIType(self.mock_logger, config)
        start_vec, stop_vec, aqi_vec = SUT.get_series(calculated_field, utils.database.timespan, TestNowcastDevelopment.db_manager)

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

if __name__ == '__main__':

    unittest.main(exit=False)
