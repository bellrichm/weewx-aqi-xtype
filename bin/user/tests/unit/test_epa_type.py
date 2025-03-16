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

class TestGetScalar(unittest.TestCase):
    def test_get_scalar_valid_inputs(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        mock_sql_executor = mock.Mock()

        calculator = user.aqitype.EPAAQI
        algorithm = 'EPAAQI'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = random_string()

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        aqi = random.randint(11, 100)
        with mock.patch.object(calculator, 'calculate', return_value=aqi):
            SUT = user.aqitype.AQIType(mock_logger, mock_sql_executor, config)

            unit = random_string()
            unit_group = random_string()

            record = {
                'usUnits': utils.database.US_UNITS,
                'interval': utils.database.ARCHIVE_INTERVAL_MINUTES,
                'dateTime': time.time(),
                input_field: random.randint(0, 10),
            }

            with mock.patch('weewx.units.getStandardUnitType', return_value=[unit, unit_group]):

                value_tuple = SUT.get_scalar(calculated_field, record)

                self.assertEqual(value_tuple[0], aqi)
                self.assertEqual(value_tuple[1], unit)
                self.assertEqual(value_tuple[2], unit_group)

class TestGetSeries(unittest.TestCase):
    def test_get_series_valid_inputs(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        mock_sql_executor = mock.Mock()
        mock_db_manager = mock.Mock()

        calculator = user.aqitype.EPAAQI
        algorithm = 'EPAAQI'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = random_string()

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        aqi = [random.randint(11, 100),
               random.randint(11, 100)]
        with mock.patch.object(calculator, 'calculate', side_effect=aqi):

            SUT = user.aqitype.AQIType(mock_logger, mock_sql_executor, config)

            unit = random_string()
            unit_group = random_string()
            now = int(time.time() + 0.5)
            end_timestamp = (int(now / utils.database.ARCHIVE_INTERVAL_SECONDS) + 1) * utils.database.ARCHIVE_INTERVAL_SECONDS

            db_records = [(end_timestamp - utils.database.ARCHIVE_INTERVAL_SECONDS,
                           utils.database.US_UNITS,
                           utils.database.ARCHIVE_INTERVAL_MINUTES,
                           random.randint(1, 50)),
                          (end_timestamp,
                           utils.database.US_UNITS,
                           utils.database.ARCHIVE_INTERVAL_MINUTES,
                           random.randint(1, 50))]

            mock_sql_executor.get_concentration_data.return_value = db_records

            with mock.patch('weewx.units.getStandardUnitType', return_value=[unit, unit_group]):
                start_vec_t, stop_vec_t, data_vec_t  = \
                    SUT.get_series(calculated_field, weeutil.weeutil.TimeSpan(end_timestamp-3600, end_timestamp), mock_db_manager)

                self.assertEqual(start_vec_t,
                                ([end_timestamp - 2 * utils.database.ARCHIVE_INTERVAL_SECONDS,
                                end_timestamp - utils.database.ARCHIVE_INTERVAL_SECONDS],
                                'unix_epoch',
                                'group_time'))
                self.assertEqual(stop_vec_t,
                                ([end_timestamp - utils.database.ARCHIVE_INTERVAL_SECONDS, end_timestamp], 'unix_epoch', 'group_time'))
                self.assertEqual(data_vec_t, (aqi, unit, unit_group))

class TestGetAggregate(unittest.TestCase):
    def test_get_aggregation_avg_valid_inputs(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        mock_sql_executor = mock.Mock()
        mock_db_manager = mock.Mock()

        calculator = user.aqitype.EPAAQI
        algorithm = 'EPAAQI'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = random_string()

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        aqi = [random.randint(11, 100),
               random.randint(11, 100)]
        with mock.patch.object(calculator, 'calculate', side_effect=aqi):
            SUT = user.aqitype.AQIType(mock_logger, mock_sql_executor, config)

            unit = random_string()
            unit_group = random_string()
            now = int(time.time() + 0.5)
            end_timestamp = (int(now / utils.database.ARCHIVE_INTERVAL_SECONDS) + 1) * utils.database.ARCHIVE_INTERVAL_SECONDS

            mock_data  = 'aggregate', [[random.randint(11, 100)], [random.randint(11, 100)]]
            mock_sql_executor.get_aggregate_concentation_data.return_value = mock_data

            with mock.patch('weewx.units.getStandardUnitType', return_value=[unit, unit_group]):

                value_tuple  = \
                    SUT.get_aggregate(calculated_field, weeutil.weeutil.TimeSpan(end_timestamp-3600, end_timestamp), 'avg', mock_db_manager)

                self.assertEqual(value_tuple[0], round(sum(aqi) / len(aqi)))
                self.assertEqual(value_tuple[1], unit)
                self.assertEqual(value_tuple[2], unit_group)

    def test_get_aggregation_min_valid_inputs(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        mock_sql_executor= mock.Mock()
        mock_db_manager = mock.Mock()

        calculator = user.aqitype.EPAAQI
        algorithm = 'EPAAQI'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = random_string()

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        aqi = random.randint(11, 100)
        with mock.patch.object(calculator, 'calculate', return_value=aqi):
            SUT = user.aqitype.AQIType(mock_logger, mock_sql_executor, config)

            unit = random_string()
            unit_group = random_string()
            now = int(time.time() + 0.5)
            end_timestamp = (int(now / utils.database.ARCHIVE_INTERVAL_SECONDS) + 1) * utils.database.ARCHIVE_INTERVAL_SECONDS

            mock_data  = random_string(), [[random.random()],]
            mock_sql_executor.get_aggregate_concentation_data.return_value = mock_data

            with mock.patch('weewx.units.getStandardUnitType', return_value=[unit, unit_group]):

                value_tuple  = \
                    SUT.get_aggregate(calculated_field, weeutil.weeutil.TimeSpan(end_timestamp-3600, end_timestamp), 'min', mock_db_manager)

                self.assertEqual(value_tuple[0], aqi)
                self.assertEqual(value_tuple[1], unit)
                self.assertEqual(value_tuple[2], unit_group)

    def test_get_aggregated_series_valid_inputs(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        mock_sql_executor = mock.Mock()
        mock_db_manager = mock.Mock()

        algorithm = 'EPAAQI'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = random_string()

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        SUT = user.aqitype.AQIType(mock_logger, mock_sql_executor (), config)

        unit = random_string()
        unit_group = random_string()
        now = int(time.time() + 0.5)
        end_timestamp = (int(now / utils.database.ARCHIVE_INTERVAL_SECONDS) + 1) * utils.database.ARCHIVE_INTERVAL_SECONDS
        start_timestamp = end_timestamp - 3600
        aggregate_interval = 1200

        timespan = weeutil.weeutil.TimeSpan(start_timestamp, end_timestamp)

        mock_db_manager.first_timestamp = start_timestamp
        mock_db_manager.last_timestamp = end_timestamp

        aqi_tuples = [(random.randint(11, 100), unit, unit_group),
                      (random.randint(11, 100), unit, unit_group),
                      (random.randint(11, 100), unit, unit_group)]
        with mock.patch.object(user.aqitype.AQIType, 'get_aggregate', side_effect=aqi_tuples):
            value_tuple  = SUT.get_series(calculated_field,
                                        timespan,
                                        mock_db_manager,
                                        aggregate_type=random_string(),
                                        aggregate_interval=aggregate_interval)

            self.assertEqual(value_tuple[0], \
                             ([start_timestamp, start_timestamp + aggregate_interval, start_timestamp + 2*aggregate_interval], \
                              'unix_epoch', \
                              'group_time'))
            self.assertEqual(value_tuple[1], \
                             ([end_timestamp - 2*aggregate_interval, end_timestamp - aggregate_interval, end_timestamp], \
                              'unix_epoch', \
                              'group_time'))
            self.assertEqual(value_tuple[2], ([aqi_tuples[0][0], aqi_tuples[1][0], aqi_tuples[2][0]], unit, unit_group))

if __name__ == '__main__':
    #test_suite = unittest.TestSuite()
    #test_suite.addTest(TestEPAAQICalculate('test_get_aggregate_min_data'))
    #unittest.TextTestRunner().run(test_suite)

    unittest.main(exit=False)
