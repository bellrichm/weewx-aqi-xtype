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
import random
import string
import time

import weeutil.weeutil

import user.aqitype

import utils.database
from utils import data

archive_intervals_in_day = 24 * 60 / utils.database.ARCHIVE_INTERVAL_MINUTES

def random_string(length=32):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(length)]) # pylint: disable=unused-variable

# ToDo: is there a better way?
def mock_calculate_effect(_1, _2, _3, _4):
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

class TestNowcastCalculate(unittest.TestCase):
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

    def test_get_concentration_data(self):
        SUT = user.aqitype.NOWCAST(self.mock_logger, random.randint(1, 100), random_string(),TestNowcastCalculate.input_field)

        # The timestamp in the template that I am using is 1740168300 (3:05 PM Eastern on 2/21/2025)
        ret_value = SUT._get_concentration_data(TestNowcastCalculate.db_manager, 1740168300)

        expected_pm_values = (1.4010919540229885, 1.4406226053639848, 1.5153544061302677,
                              1.7157567049808427, 1.4154310344827585, 1.5376532567049808,
                              1.3357950191570878, 1.5952873563218388, 1.3942241379310343,
                              1.4037739463601533, 1.1982950191570885, 1.2343007662835248)
        expected_timestamps = (1740168000, 1740164400, 1740160800, 1740157200, 1740153600, 1740150000,
                               1740146400, 1740142800, 1740139200, 1740135600, 1740132000, 1740128400)

        self.assertEqual(ret_value,
                         (12, 1.1982950191570885, 1.7157567049808427, expected_timestamps, expected_pm_values)
                        )

    def test_calculate_series_prototype(self):
        # ToDo: This 'test' will be used to develop series support for the Nowcast algorithm.
        #       Note, due to performance concerns, I am not sure the Nowcast algotithm will be supported.
        #
        print("begin")

        SUT = user.aqitype.NOWCAST(self.mock_logger, random.randint(1, 100), random_string(), TestNowcastCalculate.input_field)

        start_vec, stop_vec, concentration_vec = SUT.calculate_series(self.db_manager, utils.database.timespan, 'pm2_5')

        #print(start_vec)
        #print(stop_vec)
        #print(concentration_vec)

        self.assertEqual(start_vec,
                         [1740110400, 1740114000, 1740117600, 1740121200, 1740124800, 1740128400,
                          1740132000, 1740135600, 1740139200, 1740142800, 1740146400, 1740150000,
                          1740153600, 1740157200, 1740160800, 1740164400, 1740168000, 1740171600,
                          1740175200, 1740178800, 1740182400, 1740186000, 1740189600, 1740193200, 1740196800])
        self.assertEqual(stop_vec,
                         [1740114000, 1740117600, 1740121200, 1740124800, 1740128400, 1740132000,
                          1740135600, 1740139200, 1740142800, 1740146400, 1740150000, 1740153600,
                          1740157200, 1740160800, 1740164400, 1740168000, 1740171600, 1740175200,
                          1740178800, 1740182400, 1740186000, 1740189600, 1740193200, 1740196800, 1740200100])
        self.assertEqual(concentration_vec,
                         [1.5, 1.5, 1.4, 1.4, 1.4, 1.3,
                          1.3, 1.3, 1.3, 1.4, 1.4, 1.4,
                          1.4, 1.5, 1.5, 1.5, 1.5, 1.4,
                          1.4, 1.4, 1.4, 1.2, 1.2, 1.3, 1.3])

        print("end")

    def test_get_concentration_data_series(self):
        # ToDo: This 'test' will be used to develop series support for the Nowcast algorithm.
        #       Note, due to performance concerns, I am not sure the Nowcast algotithm will be supported.
        #
        print("begin")

        SUT = user.aqitype.NOWCAST(self.mock_logger, random.randint(1, 100), random_string(), TestNowcastCalculate.input_field)

        stop = min(weeutil.weeutil.startOfInterval(time.time(), 3600), utils.database.timespan.stop)
        stop_time = stop - 3600 * 11

        data_count, records_iter = SUT._get_concentration_data_series(self.db_manager, stop_time , utils.database.timespan.start - 43200)
        records = list(records_iter)

        #print(records)
        #print(data_count)

        self.assertEqual(data_count, 25)
        self.assertEqual(records,
                         [(1740156900, 1.6773772204806685), (1740153600, 1.4154310344827585), (1740150000, 1.5376532567049808),
                          (1740146400, 1.3357950191570878), (1740142800, 1.5952873563218388), (1740139200, 1.3942241379310343),
                          (1740135600, 1.4037739463601533), (1740132000, 1.1982950191570885), (1740128400, 1.2343007662835248),
                          (1740124800, 1.5045689655172414), (1740121200, 1.2960057471264366), (1740117600, 1.2493199233716472),
                          (1740114000, 1.7136206896551724), (1740110400, 1.6761015325670499), (1740106800, 1.3132375478927203),
                          (1740103200, 1.4535919540229882), (1740099600, 1.366609195402299), (1740096000, 1.4308908045977013),
                          (1740092400, 1.722883141762452), (1740088800, 1.364310344827586), (1740085200, 1.6051053639846746),
                          (1740081600, 1.6208045977011494), (1740078000, 1.6583045977011492), (1740074400, 1.7926724137931034),
                          (1740070800, 1.8538122605363985)])

        print("end")

class TestEPAAQICalculate(unittest.TestCase):
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
                                   TestEPAAQICalculate.input_field,
                                   TestEPAAQICalculate.algorithm,
                                   TestEPAAQICalculate.aqi_type)
        self.config = configobj.ConfigObj(config_dict)

    def test_get_series_data(self):
        with mock.patch.object(user.aqitype.EPAAQI, 'calculate', side_effect=mock_calculate_effect) as mock_calculate:
            SUT = user.aqitype.AQIType(self.mock_logger, self.config)

            with mock.patch('weewx.units.getStandardUnitType', return_value=self.unit_group):
                start_vec_t, stop_vec_t, _data_vec_t = SUT._get_series_epaaqi(self.calculated_field,
                                                                              utils.database.timespan,
                                                                              TestEPAAQICalculate.db_manager,
                                                                              None,
                                                                              None)

                mock_calculate.assert_called()
                self.assertEqual(mock_calculate.call_count, archive_intervals_in_day)

                i = 0
                for call_arg in mock_calculate.call_args_list:
                    self.assertEqual(call_arg[0][2], data.db_20250221_pm2_5_values[i])
                    self.assertEqual(stop_vec_t[0][i], data.db_20250221_timestamps[i])
                    self.assertEqual(start_vec_t[0][i], data.db_20250221_timestamps[i] - utils.database.ARCHIVE_INTERVAL_SECONDS)
                    i += 1

    def test_get_aggregate_avg_data(self):
        with mock.patch.object(user.aqitype.EPAAQI, 'calculate', side_effect=mock_calculate_effect    ) as mock_calculate:
            SUT = user.aqitype.AQIType(self.mock_logger, self.config)

            with mock.patch('weewx.units.getStandardUnitType', return_value=self.unit_group):
                _ret_value = SUT._get_aggregate_epaaqi(self.calculated_field,
                                                       utils.database.timespan,
                                                       'avg',
                                                       TestEPAAQICalculate.db_manager)

                self.assertEqual(mock_calculate.call_count, archive_intervals_in_day)

                i = 0
                for call_arg in mock_calculate.call_args_list:
                    self.assertEqual(call_arg[0][2], data.db_20250221_pm2_5_values[i])
                    i += 1

    def test_get_aggregate_min_data(self):
        with mock.patch.object(user.aqitype.EPAAQI, 'calculate', return_value=random.randint(1, 100)) as mock_calculate:
            SUT = user.aqitype.AQIType(self.mock_logger, self.config)

            with mock.patch('weewx.units.getStandardUnitType', return_value=self.unit_group):
                _ret_value = SUT._get_aggregate_epaaqi(self.calculated_field,
                                                       utils.database.timespan,
                                                       'min',
                                                       TestEPAAQICalculate.db_manager)

                mock_calculate.assert_called_once_with(TestEPAAQICalculate.db_manager,
                                                       None,
                                                       min(data.db_20250221_pm2_5_values),
                                                       TestEPAAQICalculate.aqi_type)

    def test_get_aggregate_max_data(self):
        with mock.patch.object(user.aqitype.EPAAQI, 'calculate', return_value=random.randint(1, 100)) as mock_calculate:
            SUT = user.aqitype.AQIType(self.mock_logger, self.config)

            with mock.patch('weewx.units.getStandardUnitType', return_value=self.unit_group):
                _ret_value = SUT._get_aggregate_epaaqi(self.calculated_field,
                                                       utils.database.timespan,
                                                       'max',
                                                       self.db_manager)

                mock_calculate.assert_called_once_with(TestEPAAQICalculate.db_manager,
                                                       None,
                                                       max(data.db_20250221_pm2_5_values),
                                                       TestEPAAQICalculate.aqi_type)

if __name__ == '__main__':
    test_suite = unittest.TestSuite()
    #test_suite.addTest(TestNowcastCalculate('test_get_concentration_data_series'))
    test_suite.addTest(TestNowcastCalculate('test_calculate_series_prototype'))
    unittest.TextTestRunner().run(test_suite)

    #unittest.main(exit=False)
