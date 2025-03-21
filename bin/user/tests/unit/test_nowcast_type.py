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
import types

import weeutil

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

class TestGetScalarNowCast(unittest.TestCase):
    def test_get_scalar_valid_inputs(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        mock_sql_executor = mock.Mock()
        mock_db_manager = mock.Mock()

        calculator = user.aqitype.NowCast
        algorithm = 'NowCast'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = random_string()

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        aqi = random.randint(11, 100)
        with mock.patch.object(calculator, 'calculate', return_value=(random_string(), [], [], [aqi])):
            SUT = user.aqitype.AQIType(mock_logger, mock_sql_executor, config)

            unit = random_string()
            unit_group = random_string()

            record = {
                'usUnits': utils.database.US_UNITS,
                'interval': utils.database.ARCHIVE_INTERVAL_MINUTES,
                'dateTime': time.time(),
                input_field: random.randint(0, 10),
            }

            mock_sql_executor.get_concentration_data_nowcast.return_value = iter([])
            with mock.patch('weewx.units.getStandardUnitType', return_value=[unit, unit_group]):
                value_tuple = SUT.get_scalar(calculated_field, record, mock_db_manager)

                self.assertEqual(value_tuple[0], aqi)
                self.assertEqual(value_tuple[1], unit)
                self.assertEqual(value_tuple[2], unit_group)

class TestNowCastGetSeries(unittest.TestCase):
    def test_get_series_valid_inputs(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        mock_sql_executor = mock.Mock()
        mock_db_manager = mock.Mock()

        calculator = user.aqitype.NowCast
        algorithm = 'NowCast'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = utils.database.PM2_5_INPUT_FIELD

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        mock_start_vec = []
        mock_stop_vec = []
        mock_aqi_vec = []
        for _ in range(random.randint(2, 11)):
            mock_has_data = random_string()
            mock_start_vec.append(random.randint(101,200))
            mock_start_vec.append(random.randint(201,300))
            mock_aqi_vec.append(random.randint(1,100))

        with mock.patch.object(calculator, 'calculate', return_value=(mock_has_data, mock_start_vec, mock_stop_vec, mock_aqi_vec)):
            SUT = user.aqitype.AQIType(mock_logger, mock_sql_executor, config)

            unit = random_string()
            unit_group = random_string()

            with mock.patch('weewx.units.getStandardUnitType', return_value=[unit, unit_group]):
                start_vec, stop_vec, aqi_vec = SUT.get_series(calculated_field, utils.database.timespan, mock_db_manager)

                self.assertEqual(start_vec, (mock_start_vec, 'unix_epoch', 'group_time'))
                self.assertEqual(stop_vec, (mock_stop_vec, 'unix_epoch', 'group_time'))
                self.assertEqual(aqi_vec, (mock_aqi_vec, unit, unit_group))

        print("done")

    def test_get_series_timespan_too_short(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        mock_sql_executor = mock.Mock()
        mock_db_manager = mock.Mock()

        algorithm = 'NowCast'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = utils.database.PM2_5_INPUT_FIELD

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)
        timespan = weeutil.weeutil.TimeSpan(utils.database.timespan.start,
                                            utils.database.timespan.start + 3600 - 5)

        SUT = user.aqitype.AQIType(mock_logger, mock_sql_executor, config)

        unit = random_string()
        unit_group = random_string()

        with mock.patch('weewx.units.getStandardUnitType', return_value=[unit, unit_group]):
            start_vec, stop_vec, aqi_vec = SUT.get_series(calculated_field, timespan, mock_db_manager)

            self.assertEqual(start_vec, ([], 'unix_epoch', 'group_time'))
            self.assertEqual(stop_vec, ([], 'unix_epoch', 'group_time'))
            self.assertEqual(aqi_vec, ([], unit, unit_group))

    def test_get_series_aggregate(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        mock_sql_executor = mock.Mock()
        mock_db_manager = mock.Mock()

        algorithm = 'NowCast'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = utils.database.PM2_5_INPUT_FIELD

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        SUT = user.aqitype.AQIType(mock_logger, mock_sql_executor, config)

        unit = random_string()
        unit_group = random_string()

        aggregate_interval = 3600

        now = int(time.time() + 0.5)
        end_timestamp = (int(now / utils.database.ARCHIVE_INTERVAL_SECONDS) + 1) * utils.database.ARCHIVE_INTERVAL_SECONDS
        start_timestamp = end_timestamp - 10800

        timespan = weeutil.weeutil.TimeSpan(start_timestamp, end_timestamp)

        timespans = []
        timestamp = start_timestamp
        while timestamp < end_timestamp:
            timespans.append(weeutil.weeutil.TimeSpan(timestamp, timestamp + aggregate_interval))
            timestamp += aggregate_interval

        mock_db_manager.first_timestamp = start_timestamp
        mock_db_manager.last_timestamp = end_timestamp

        aqi_tuples = [(random.randint(11, 100), unit, unit_group),
                      (random.randint(11, 100), unit, unit_group),
                      (random.randint(11, 100), unit, unit_group)]

        with mock.patch('weewx.units.getStandardUnitType', return_value=[unit, unit_group]):
            with mock.patch('weeutil.weeutil.intervalgen', return_value=timespans):
                with mock.patch.object(user.aqitype.AQIType, 'get_aggregate', side_effect=aqi_tuples):
                    value_tuple = SUT.get_series(calculated_field,
                                                timespan,
                                                mock_db_manager,
                                                aggregate_type=random_string(),
                                                aggregate_interval='hour') # ToDo: temp until mocking done

                self.assertEqual(value_tuple[0], \
                                ([start_timestamp, start_timestamp + aggregate_interval, start_timestamp + 2*aggregate_interval], \
                                'unix_epoch', \
                                'group_time'))
                self.assertEqual(value_tuple[1], \
                                ([end_timestamp - 2*aggregate_interval, end_timestamp - aggregate_interval, end_timestamp], \
                                'unix_epoch', \
                                'group_time'))
                self.assertEqual(value_tuple[2], ([aqi_tuples[0][0], aqi_tuples[1][0], aqi_tuples[2][0]], unit, unit_group))

class TestNowCastGetAggregate(unittest.TestCase):
    def test_get_aggregate_type_not_null(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        mock_sql_executor = mock.Mock()
        mock_db_manager = mock.Mock()

        calculator = user.aqitype.NowCast
        algorithm = 'NowCast'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = utils.database.PM2_5_INPUT_FIELD

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        mock_value = (
            types.SimpleNamespace(not_null=True),
            random_string(),
            random_string(),
            random_string()
        )

        with mock.patch.object(calculator, 'calculate', return_value=mock_value):
            SUT = user.aqitype.AQIType(mock_logger, mock_sql_executor, config)

            unit = random_string()
            unit_group = random_string()

            with mock.patch('weewx.units.getStandardUnitType', return_value=[unit, unit_group]):
                aggregate_value = SUT.get_aggregate(calculated_field, utils.database.timespan, 'not_null', mock_db_manager)

                self.assertEqual(aggregate_value, (True, unit, unit_group))

if __name__ == '__main__':
    #test_suite = unittest.TestSuite()
    #test_suite.addTest(TestNowCastGetSeries('test_get_series_aggregate'))
    #unittest.TextTestRunner().run(test_suite)

    unittest.main(exit=False)
