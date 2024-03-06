#    Copyright (c) 2023-2024 Rich Bell <bellrichm@gmail.com>
#    See the file LICENSE.txt for your full rights.

"""
WeeWX XTypes extensions that add new types of AQI.
"""

import logging
import math
import sys
import time

from collections import ChainMap

import weedb
import weeutil
import weewx
import weewx.cheetahgenerator
from weewx.engine import StdService
from weewx.units import ValueTuple
from weeutil.weeutil import to_bool, to_int

VERSION = '1.2.0-rc01'

class Logger:
    '''
    Manage the logging
    '''
    def __init__(self):
        self.log = logging.getLogger(__name__)

    def logdbg(self, msg):
        """ log debug messages """
        self.log.debug(msg)

    def loginf(self, msg):
        """ log informational messages """
        self.log.info(msg)

    def logerr(self, msg):
        """ log error messages """
        self.log.error(msg)

class AQITypeManager(StdService):
    """ A class to manage the registration of the AQI XType"""
    def __init__(self, engine, config_dict):
        super().__init__(engine, config_dict)

        # ToDo: Capture the archive_interval
        # https://groups.google.com/g/weewx-user/c/W0jG1kElJ1k/m/9tjnkrzfAwAJ?utm_medium=email&utm_source=footer

        self.logger = Logger()

        if 'aqitype' not in config_dict:
            raise ValueError("[aqitype] Needs to be configured")

        self._setup(config_dict['aqitype'])

        self.logger.loginf("Adding AQI type to the XTypes pipeline.")
        self.aqi = AQIType(self.logger, config_dict['aqitype'])
        if to_bool(config_dict['aqitype'].get('prepend', True)):
            weewx.xtypes.xtypes.insert(0, self.aqi)
        else:
            weewx.xtypes.xtypes.append(self.aqi)

    def _setup(self, config_dict):
        unit_group = config_dict.get('unit_group', 'group_aqi')
        unit = config_dict.get('unit', 'aqi')

        weewx.units.USUnits[unit_group] = unit
        weewx.units.MetricUnits[unit_group] = unit
        weewx.units.MetricWXUnits[unit_group] = unit

        weewx.units.default_unit_format_dict[unit]  = '%d'
        weewx.units.default_unit_label_dict[unit]  = ''

        for xtype in config_dict.sections:
            weewx.units.obs_group_dict[xtype] = unit_group

    def shutDown(self):
        """Run when an engine shutdown is requested."""
        weewx.xtypes.xtypes.remove(self.aqi)

class AbstractCalculator():
    """
    Abstract Calculator class.
    """
    def calculate(self, db_manager, time_stamp, reading, aqi_type):
        """
        Perform the calculation.
        """
        raise NotImplementedError

class NOWCAST(AbstractCalculator):
    """
    Class for calculating the Nowcast AQI.
    Additional information:
    https://usepa.servicenowservices.com/airnow?id=kb_article_view&sys_id=bb8b65ef1b06bc10028420eae54bcb98&spa=1
    https://www3.epa.gov/airnow/aqicalctest/nowcast.htm
    """

    readings = {'pm2_5', 'pm10'}

    def __init__(self, logger, log_level,  sub_calculator, sub_field_name):
        self.logger = logger
        self.log_level = log_level
        self.sub_calculator = sub_calculator
        self.sub_field_name = sub_field_name

    def  _logdbg(self, msg):
        if self.log_level <= 10:
            self.logger.logdbg(f"(NOWCAST) {msg}")

    def _loginf(self, msg):
        if self.log_level <= 20:
            self.logger.loginf(f"(NOWCAST) {msg}")

    def _logerr(self, msg):
        if self.log_level <= 40:
            self.logger.logerr(f"(NOWCAST) {msg}")

    def _get_concentration_data(self, db_manager, stop):
        # Get the necessary concentration data to compute for a given time
        start = stop - 43200
        # ToDo: need to get this from the 'console'
        archive_interval = 300

        stats_sql_str = f'''
        Select COUNT(rowStats.avgConcentration) as rowCount,
            MIN(rowStats.avgConcentration) as rowMin,
            MAX(rowStats.avgConcentration) as rowMax
        FROM (
                SELECT avg({self.sub_field_name}) as avgConcentration
                FROM archive
            WHERE dateTime >= {start} + 3600 + {archive_interval}
                AND dateTime < {stop} + 3600
            /* need to subtract the archive interval to get the correct begin and end range */
            GROUP BY (dateTime - {archive_interval}) / 3600
            ) AS rowStats
        '''

        sql_str = f'''
        SELECT
            MAX(dateTime),
            avg({self.sub_field_name}) as avgConcentration
        FROM archive
            /* 300 is the archive interval */
            WHERE dateTime >= {start} + 3600 + {archive_interval}
                AND dateTime < {stop} + 3600
            /* need to subtract the archive interval to get the correct begin and end range */
            GROUP BY (dateTime - {archive_interval}) / 3600
            HAVING avgConcentration IS NOT NULL
            ORDER BY dateTime DESC
        '''

        try:
            # Only one record is returned
            record_stats = db_manager.getSql(stats_sql_str)
        except weedb.NoColumnError:
            raise weewx.UnknownType(self.sub_field_name) from weedb.NoColumnError

        try:
            # Max of 12 is returned, grab them all and be done with it
            record = list(db_manager.genSql(sql_str))
            timestamps, data = zip(*record)
        except weedb.NoColumnError:
            raise weewx.UnknownType(self.sub_field_name) from weedb.NoColumnError

        return record_stats[0], record_stats[1], record_stats[2], timestamps, data

    def _get_concentration_data_series(self, db_manager, stop, start):
        # Get the necessary concentration data to compute for a given time

        # ToDo: need to get this from the 'console'
        archive_interval = 300

        stats_sql_str = f'''
        Select COUNT(rowStats.avgConcentration) as rowCount
        FROM (
                SELECT avg({self.sub_field_name}) as avgConcentration
                FROM archive
            WHERE dateTime >= {start} + {archive_interval}
                AND dateTime < {stop}
            /* need to subtract the archive interval to get the correct begin and end range */
            GROUP BY (dateTime - {archive_interval}) / 3600
            ) AS rowStats
        '''

        sql_str = f'''
        SELECT
            MAX(dateTime),
            avg({self.sub_field_name}) as avgConcentration
        FROM archive
            /* 300 is the archive interval */
            WHERE dateTime >= {start}+ {archive_interval}
                AND dateTime < {stop}
            /* need to subtract the archive interval to get the correct begin and end range */
            GROUP BY (dateTime - {archive_interval}) / 3600
            ORDER BY dateTime DESC
        '''

        try:
            # Only one record is returned
            record_stats = db_manager.getSql(stats_sql_str)
        except weedb.NoColumnError:
            raise weewx.UnknownType(self.sub_field_name) from weedb.NoColumnError

        return record_stats[0], db_manager.genSql(sql_str)

    def calculate_concentration(self, current_hour, data_count, data_min, data_max, timestamps, concentrations):
        '''
        Calculate the nowcast concentration.
        '''

        two_hours_ago = current_hour - 7200

        # Missing data: 2 of the last 3 hours of data must be valid for a NowCast calculation.
        if data_count < 3:
            self._logdbg(f"Less than 3 readings ({data_count}).")
            raise weewx.CannotCalculate()

        if timestamps[1] <= two_hours_ago:
            self._logdbg(f"Of {data_count} readings, at least need to be within the last 2 hours ")
            raise weewx.CannotCalculate()

        data_range = data_max - data_min
        scaled_rate_change = data_range/data_max
        weight_factor = max((1-scaled_rate_change), .5)
        numerator = 0
        denominator = 0
        for i in range(data_count):
            hours_ago = int((current_hour - timestamps[i]) / 3600 + 1)
            self._logdbg(f"Hours ago: {hours_ago} pm was: {concentrations[i]}")
            numerator += concentrations[i] * (weight_factor ** hours_ago)
            denominator += weight_factor ** hours_ago

        concentration = math.trunc((numerator / denominator) * 10) / 10
        self._logdbg(f"The computed concentration is {concentration}")

        return concentration

    def calculate(self, db_manager, time_stamp, reading, aqi_type):
        self._logdbg(f"The time stamp is {time_stamp}.")
        self._logdbg(f"The type is '{aqi_type}'")

        if time_stamp is None:
            raise weewx.CannotCalculate()

        current_hour = weeutil.weeutil.startOfInterval(time_stamp, 3600)
        data_count, data_min, data_max, timestamps, concentrations = self._get_concentration_data(db_manager, current_hour)

        concentration = self.calculate_concentration(current_hour, data_count, data_min, data_max, timestamps, concentrations)
        aqi = self.sub_calculator.calculate(None, None, concentration, aqi_type)
        self._logdbg(f"The computed AQI is {aqi}")

        return aqi

    def calculate_series(self, db_manager, timespan, aqi_type):
        self._logdbg(f"The time stamp is {timespan}.")
        self._logdbg(f"The type is '{aqi_type}'")
        stop = min(weeutil.weeutil.startOfInterval(time.time(), 3600), timespan.stop)

        _data_count, _data_min, _data_max, timestamps, concentrations = self._get_concentration_data(db_manager, stop)
        timestamps = list(timestamps)
        concentrations = list(concentrations)

        del timestamps[0]
        del concentrations[0]
        concentration_vec = []
        stop_vec = []
        stop_time = stop - 3600 * 11
        stop2 = timestamps[0]
        data_count, records = self._get_concentration_data_series(db_manager, stop_time , timespan.start - 43200)
        for record in records:
            timestamps.append(record[0])
            if len(timestamps) > 12:
                del timestamps[0]

            concentrations.append(record[1])
            if len(concentrations) > 12:
                del concentrations[0]

            stop_vec.append(record[0] + 43200)
            stop2 -= 3600
            if record[1] is not None:
                try:
                    concentration_vec.append(self.calculate_concentration(timestamps[0],
                                                                          len(concentrations),
                                                                          min(concentrations),
                                                                          max(concentrations),
                                                                          timestamps,
                                                                          concentrations))
                except weewx.CannotCalculate:
                    concentration_vec.append(None)
            else:
                concentration_vec.append(None)

        start_vec = list(stop_vec[1:])
        start_vec.append(start_vec[-1] - 3600)
        start_vec.reverse()
        stop_vec.reverse()
        concentration_vec.reverse()

        return start_vec, stop_vec, concentration_vec

class EPAAQI(AbstractCalculator):
    """
    Class for calculating the EPA'S AQI.
    """

    aqi_bp = [
        {'min': 0, 'max': 50, 'color': '00e400'},
        {'min': 51, 'max': 100, 'color': 'ffff00'},
        {'min': 101, 'max': 150, 'color': 'ff7e00'},
        {'min': 151, 'max': 200, 'color': 'ff0000'},
        {'min': 201, 'max': 300, 'color': '8f3f97'},
        {'min': 301, 'max': 400, 'color': '7e0023'},
        {'min': 401, 'max': 500, 'color': '7e0023'},
    ]

    readings = {
        'pm2_5': {
            'prep_data': lambda x: math.trunc(x * 10) / 10,
            'breakpoints': [
                {'min': 0.0, 'max': 12.0},
                {'min': 12.1, 'max': 35.4},
                {'min': 35.5, 'max': 55.4},
                {'min': 55.5, 'max': 150.4},
                {'min': 150.5, 'max': 250.4},
                {'min': 250.5, 'max': 350.4},
                {'min': 350.5, 'max': 500.4,},
            ]
        },
        'pm10': {
            'prep_data': lambda x: math.trunc(x), # pylint: disable=unnecessary-lambda
            'breakpoints': [
                {'min': 0.0, 'max': 54},
                {'min': 55, 'max': 154},
                {'min': 155, 'max': 254},
                {'min': 255, 'max': 354},
                {'min': 355, 'max': 424},
                {'min': 425, 'max': 504},
                {'min': 505, 'max': 604},
            ]
        }
    }

    def __init__(self, logger, log_level, sub_calculator, sub_field_name): # Need to match signature pylint: disable=unused-argument
        self.logger = logger
        self.log_level = log_level

    def  _logdbg(self, msg):
        if self.log_level <= 10:
            self.logger.logdbg(f"(EPAAQI) {msg}")

    def _loginf(self, msg):
        if self.log_level <= 20:
            self.logger.loginf(f"(EPAAQI) {msg}")

    def _logerr(self, msg):
        if self.log_level <= 40:
            self.logger.logerr(f"(EPAAQI) {msg}")

    def calculate(self, db_manager, time_stamp, reading, aqi_type):
        '''
        Calculate the AQI.
        Additional information:
        https://www.airnow.gov/publications/air-quality-index/technical-assistance-document-for-reporting-the-daily-aqi/
        https://www.airnow.gov/aqi/aqi-calculator-concentration/
        '''

        self._logdbg(f"The input value is {reading}.")
        self._logdbg(f"The type is '{aqi_type}'")

        if reading is None:
            return reading

        readings = EPAAQI.readings[aqi_type]

        breakpoint_count = len(readings['breakpoints'])
        index = 0
        while index < breakpoint_count:
            if reading < readings['breakpoints'][index]['max']:
                break
            index += 1

        if index >= breakpoint_count:
            index =  len(readings['breakpoints']) - 1

        reading_bp_max = readings['breakpoints'][index]['max']
        reading_bp_min = readings['breakpoints'][index]['min']

        aqi_bp_max = EPAAQI.aqi_bp[index]['max']
        aqi_bp_min = EPAAQI.aqi_bp[index]['min']

        self._logdbg(f"The AQI breakpoint index is {index},  max is {aqi_bp_max}, and the min is {aqi_bp_min}.")
        self._logdbg(f"The reading breakpoint max is {reading_bp_max:f} and the min is {reading_bp_min:f}.")

        aqi = round(((aqi_bp_max - aqi_bp_min)/(reading_bp_max - reading_bp_min) * (reading - reading_bp_min)) + aqi_bp_min)

        self._logdbg(f"The computed AQI is {aqi}")

        return aqi

class AQIType(weewx.xtypes.XType):
    """
    AQI XType which computes the AQI (air quality index) from
    the pm2_5 value.
    """

    def __init__(self, logger, config_dict):
        self.logger = logger
        self.aqi_fields = {}
        for field in config_dict.sections:
            self.aqi_fields[field] = config_dict[field]
        default_log_level = config_dict.get('log_level', 20)

        for field, field_option in self.aqi_fields.items():
            sub_calculator = None
            sub_field_name = None
            log_level = to_int(config_dict[field].get('log_level', default_log_level))
            if field_option['algorithm'] == 'NOWCAST':
                if field_option['type'] not in NOWCAST.readings:
                    raise ValueError(f"Algorithm 'NOWCAST' is not supported for pollutant '{field_option['type']}'")
                field_option['support_aggregation'] = False
                field_option['support_series'] = False
                sub_calculator = getattr(sys.modules[__name__], 'EPAAQI')(self.logger, log_level, None, None)
                sub_field_name = field_option['input']
                field_option['get_aggregate'] = self._get_aggregate_nowcast
                field_option['get_series'] = self._get_series_nowcast
            else:
                if field_option['type'] not in EPAAQI.readings:
                    raise ValueError(f"Algorithm 'EPAAQI' is not supported for pollutant '{field_option['type']}'")
                field_option['support_aggregation'] = True
                field_option['support_series'] = True
                field_option['get_aggregate'] = self._get_aggregate_epaaqi
                field_option['get_series'] = self._get_series_epaaqi
            field_option['calculator']  = \
                  getattr(sys.modules[__name__], field_option['algorithm'])(self.logger, log_level, sub_calculator, sub_field_name)

        self.simple_sql_stmts = {
        'count': "SELECT COUNT(dateTime) FROM {table_name} "
                 "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL",
        'firsttime': "SELECT MIN(dateTime) FROM {table_name} "
               "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL "
               "ORDER BY dateTime ASC LIMIT 1;",
        'lasttime': "SELECT MAX(dateTime) FROM {table_name} "
               "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL "
               "ORDER BY dateTime DESC LIMIT 1;",                 
        'maxtime': "SELECT dateTime FROM {table_name} "
                   "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL "
                   "ORDER BY {input} DESC LIMIT 1", 
        'mintime': "SELECT dateTime FROM {table_name} "
                   "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL "
                   "ORDER BY {input} ASC LIMIT 1",
        'not_null': "SELECT 1 FROM {table_name} "
                    "WHERE dateTime > {start} AND dateTime <= {stop} "
                    "AND {input} IS NOT NULL LIMIT 1",                   
        }

        self.agg_sql_stmts = {
        'avg': "SELECT {input} FROM {table_name} "
               "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL",
        'sum': "SELECT {input} FROM {table_name} "
               "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL",
        }

        self.sql_stmts = {
        'first': "SELECT {input} FROM {table_name} "
               "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL "
               "ORDER BY dateTime ASC LIMIT 1;",
        'last': "SELECT {input} FROM {table_name} "
               "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL "
               "ORDER BY dateTime DESC LIMIT 1;",
        'min': "SELECT {input} FROM {table_name} "
               "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL "
               "ORDER BY {input} ASC LIMIT 1;",
        'max': "SELECT {input} FROM {table_name} "
               "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL "
               "ORDER BY {input} DESC LIMIT 1;",
    }

    def _logdbg(self, msg):
        self.logger.logdbg(f"(XTYPE) {msg}")

    def _loginf(self, msg):
        self.logger.loginf(f"(XTYPE) {msg}")

    def _logerr(self, msg):
        self.logger.logerr(f"(XTYPE) {msg}")

    def get_scalar(self, obs_type, record, db_manager=None, **option_dict):
        """ Calculate the scalar value."""
        if obs_type not in self.aqi_fields:
            raise weewx.UnknownType(obs_type)
        if record is None:
            raise weewx.CannotCalculate(obs_type)

        dependent_field = self.aqi_fields[obs_type]["input"]
        if dependent_field not in record:
            raise weewx.CannotCalculate(obs_type)
        if record[dependent_field] is None:
            raise weewx.CannotCalculate(obs_type)

        aqi_type = self.aqi_fields[obs_type]['type']

        try:
            aqi = self.aqi_fields[obs_type]['calculator'].calculate(db_manager, record['dateTime'], record[dependent_field], aqi_type)
        except weewx.CannotCalculate as exception:
            raise weewx.CannotCalculate(obs_type) from exception

        unit_type, group = weewx.units.getStandardUnitType(record['usUnits'], obs_type)
        return weewx.units.ValueTuple(aqi, unit_type, group)

    def get_series(self, obs_type, timespan, db_manager, aggregate_type=None, aggregate_interval=None, **option_dict):
        """ Calculate the series. """
        if obs_type not in self.aqi_fields:
            raise weewx.UnknownType(obs_type)
        return self.aqi_fields[obs_type]['get_series'](obs_type, timespan, db_manager, aggregate_type, aggregate_interval, **option_dict)

    def _get_series_nowcast(self, obs_type, timespan, db_manager, aggregate_type, aggregate_interval, **option_dict):
        # For now the NOWCAST algorithm does not support 'series'
        # Because XTypeTable will also try, an empty 'set' of data is returned.
        unit, unit_group = weewx.units.getStandardUnitType(db_manager.std_unit_system, obs_type, aggregate_type)

        aqi_type = self.aqi_fields[obs_type]['type']
        start_list, stop_list, concentration_list = self.aqi_fields[obs_type]['calculator'].calculate_series(db_manager, timespan, aqi_type)

        return (ValueTuple(start_list, 'unix_epoch', 'group_time'),
                ValueTuple(stop_list, 'unix_epoch', 'group_time'),
                ValueTuple(concentration_list, unit, unit_group))

    def _get_series_epaaqi(self, obs_type, timespan, db_manager, aggregate_type, aggregate_interval, **option_dict):
        aqi_type = self.aqi_fields[obs_type]['type']

        dependent_field = self.aqi_fields[obs_type]['input']

        start_vec = []
        stop_vec = []
        data_vec = []
        unit = None
        unit_group = None

        if aggregate_type:
            startstamp, stopstamp = timespan
            for stamp in weeutil.weeutil.intervalgen(startstamp, stopstamp, aggregate_interval):
                if db_manager.first_timestamp is None or stamp.stop <= db_manager.first_timestamp:
                    continue
                if db_manager.last_timestamp is None or stamp.start >= db_manager.last_timestamp:
                    break

                try:
                    agg_vt = self.get_aggregate(obs_type, stamp, aggregate_type, db_manager, **option_dict)
                except weewx.CannotCalculate:
                    agg_vt = ValueTuple(None, unit, unit_group)

                if unit:
                    if agg_vt[1] is not None and (unit != agg_vt[1] or unit_group != agg_vt[2]):
                        raise weewx.UnsupportedFeature("Cannot change units within a series.")
                else:
                    unit, unit_group = agg_vt[1], agg_vt[2]

                start_vec.append(stamp.start)
                stop_vec.append(stamp.stop)
                data_vec.append(agg_vt[0])
        else:
            std_unit_system = None
            sql_str = f'SELECT dateTime, usUnits, `interval`, {dependent_field} FROM {db_manager.table_name} ' \
                        'WHERE dateTime >= ? AND dateTime <= ?'

            try:
                for record in db_manager.genSql(sql_str, timespan):
                    aqi = None
                    timestamp, unit_system, interval, input_value = record
                    if std_unit_system:
                        if std_unit_system != unit_system:
                            raise weewx.UnsupportedFeature("Unit type cannot change within a time interval.")
                    else:
                        std_unit_system = unit_system

                    try:
                        aqi = self.aqi_fields[obs_type]['calculator'].calculate(db_manager, None, input_value, aqi_type)
                    except weewx.CannotCalculate:
                        aqi = None

                    start_vec.append(timestamp - interval * 60)
                    stop_vec.append(timestamp)
                    data_vec.append(aqi)

            except weedb.NoColumnError:
                raise weewx.UnknownType(obs_type) from weedb.NoColumnError

            unit, unit_group = weewx.units.getStandardUnitType(std_unit_system, obs_type, aggregate_type)

        return (ValueTuple(start_vec, 'unix_epoch', 'group_time'),
                ValueTuple(stop_vec, 'unix_epoch', 'group_time'),
                ValueTuple(data_vec, unit, unit_group))

    def get_aggregate(self, obs_type, timespan, aggregate_type, db_manager, **option_dict):
        """ Compute the aggregate. """
        if obs_type not in self.aqi_fields:
            raise weewx.UnknownType(obs_type)
        return self.aqi_fields[obs_type]['get_aggregate'](obs_type, timespan, aggregate_type, db_manager, **option_dict)

    def _get_aggregate_nowcast(self, obs_type, timespan, aggregate_type, db_manager, **option_dict):
       # For now the NOWCAST algorithm does not support 'aggregation'
        # Because XTypeTable will also try, 'None' is returned.
        if aggregate_type != 'not_null':
            aggregate_value = None
            # raise weewx.UnknownAggregation(aggregate_type)

        else:
            dependent_field = self.aqi_fields[obs_type]['input']

            interpolation_dict = {
                'start': timespan.start,
                'stop': timespan.stop,
                'table_name': db_manager.table_name,
                'input': dependent_field
            }

            # This is not accurate
            # Just because there is one concentration reading does not mean NOWCAST can be computed
            sql_stmt = self.simple_sql_stmts[aggregate_type].format(**interpolation_dict)

            try:
                row = db_manager.getSql(sql_stmt)
            except weedb.NoColumnError:
                raise weewx.UnknownType(obs_type) from weedb.NoColumnError

            if not row or None in row:
                aggregate_value = None
            else:
                aggregate_value = row[0]

        unit_type, group = weewx.units.getStandardUnitType(db_manager.std_unit_system, obs_type, aggregate_type)
        return weewx.units.ValueTuple(aggregate_value, unit_type, group)

    def _get_aggregate_epaaqi(self, obs_type, timespan, aggregate_type, db_manager, **option_dict):
        sql_stmts = ChainMap(self.agg_sql_stmts, self.simple_sql_stmts, self.sql_stmts)
        if aggregate_type not in sql_stmts:
            raise weewx.UnknownAggregation(aggregate_type)

        dependent_field = self.aqi_fields[obs_type]['input']
        aqi_type = self.aqi_fields[obs_type]['type']

        interpolation_dict = {
            'start': timespan.start,
            'stop': timespan.stop,
            'table_name': db_manager.table_name,
            'input': dependent_field
        }

        sql_stmt = sql_stmts[aggregate_type].format(**interpolation_dict)

        if aggregate_type in self.agg_sql_stmts:
            input_values = []
            aggregate_value = None
            try:
                for row in db_manager.genSql(sql_stmt):

                    try:
                        input_value = self.aqi_fields[obs_type]['calculator'].calculate(db_manager, None, row[0], aqi_type)
                    except weewx.CannotCalculate:
                        input_value = None

                    if input_value is not None:
                        input_values.append(input_value)
            except weedb.NoColumnError:
                raise weewx.UnknownType(obs_type) from weedb.NoColumnError

            if input_values:
                aggregate_value = sum(input_values)
                if aggregate_type == 'avg':
                    aggregate_value = round(aggregate_value / len(input_values))
        else:
            try:
                row = db_manager.getSql(sql_stmt)
            except weedb.NoColumnError:
                raise weewx.UnknownType(obs_type) from weedb.NoColumnError

            if not row or None in row:
                input_value = None
            else:
                input_value = row[0]

            if aggregate_type in self.simple_sql_stmts:
                aggregate_value = input_value
            else:
                try:
                    aggregate_value = self.aqi_fields[obs_type]['calculator'].calculate(db_manager, None, input_value, aqi_type)
                except weewx.CannotCalculate:
                    aggregate_value = None

        unit_type, group = weewx.units.getStandardUnitType(db_manager.std_unit_system, obs_type, aggregate_type)

        return weewx.units.ValueTuple(aggregate_value, unit_type, group)

class AQISearchList(weewx.cheetahgenerator.SearchList):
    """ Implement tags used by templates in the skin. """
    def __init__(self, generator):
        weewx.cheetahgenerator.SearchList.__init__(self, generator)

        self.logger = Logger()

    def get_extension_list(self, _timespan, _db_lookup):
        """ Get the extension list. """
        search_list_extension = {'AQIColor': self.get_aqi_color,
                                 'AQIDescription': self.get_aqi_description,
                                 'logdbg': self._logdbg,
                                 'loginf': self._loginf,
                                 'logerr': self._logerr,
                                 'version': VERSION,
                                }

        return [search_list_extension]

    def _logdbg(self, msg):
        self.logger.logdbg(f"(SLE) {msg}")

    def _loginf(self, msg):
        self.logger.loginf(f"(SLE) {msg}")

    def _logerr(self, msg):
        self.logger.logerr(f"(SLE) {msg}")

    def get_aqi_color(self, value, standard):
        """ Given an AQI value and standard, return the corresponding color"""
        aqi_bp = getattr(sys.modules[__name__], standard).aqi_bp
        index = self._get_index(aqi_bp, value)

        return aqi_bp[index]['color']

    def get_aqi_description(self, value, standard):
        """ Given an AQI value and standard, return the corresponding description"""
        aqi_bp = getattr(sys.modules[__name__], standard).aqi_bp
        level = self._get_index(aqi_bp, value) + 1

        return f"aqi_{standard}_description{level}"

    def _get_index(self, breakpoints, value):
        breakpoint_count = len(breakpoints)
        index = 0
        while index < breakpoint_count:
            if value < breakpoints[index]['max']:
                break
            index += 1

        if index >= breakpoint_count:
            index =  len(breakpoints) - 1

        return index
    