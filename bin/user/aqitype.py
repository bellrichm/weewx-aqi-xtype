#    Copyright (c) 2023-2025 Rich Bell <bellrichm@gmail.com>
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

VERSION = '2.0.0-rc03'

class CalculationError(Exception):
    ''' Error calculating AQI '''

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
    def calculate(self, db_manager, aqi_type, inputs):
        """
        Perform the calculation.
        """
        raise NotImplementedError

class NOWCAST(AbstractCalculator):
    """
    Class for calculating the Nowcast AQI.
    Additional information:
    https://usepa.servicenowservices.com/airnow?id=kb_article_view&sys_id=bb8b65ef1b06bc10028420eae54bcb98&spa=1

    https://www.epa.gov/sites/default/files/2018-01/documents/nowcastfactsheet.pdf
    https://mazamascience.github.io/AirMonitor/articles/NowCast.html
    http://cran.nexr.com/web/packages/PWFSLSmoke/vignettes/NowCast.html
    https://forum.airnowtech.org/t/the-nowcast-for-pm2-5-and-pm10/172
    
    https://mazamascience.github.io/AirMonitor/articles/NowCast.html#does-most-recent-include-current
    - Another reason for including the “current” hour in the NowCast “three most recent hours” is for speed of updates. 
    Suppose it is 12:04, and a measurement just came in at 12:00 (the Hour 11 measurement). 
    It would be inappropriate to wait until 13:00 to calculate the updated NowCast value. 
    For this reason, we calculate NowCast values using the monitored data for the “current” hour and the N−1 prior hours.
    - As a result of this convention, timestamps are usually an entire hour (or more) earlier than 
    the time the measurements were actually taken (exact differences depend on several factors).
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

    def calculate_concentration(self, time_stamp, data_count, data_min, data_max, timestamps, concentrations):
        '''
        Calculate the nowcast concentration.
        '''
        current_hour = weeutil.weeutil.startOfInterval(time_stamp, 3600)

        try:
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
                if concentrations[i] is not None:
                    hours_ago = int((current_hour - timestamps[i]) / 3600 + 1)
                    self._logdbg(f"Hours ago: {hours_ago} pm was: {concentrations[i]}")
                    numerator += concentrations[i] * (weight_factor ** hours_ago)
                    denominator += weight_factor ** hours_ago

            concentration = math.trunc((numerator / denominator) * 10) / 10
            self._logdbg(f"The computed concentration is {concentration}")

            return concentration
        except weewx.CannotCalculate as exception:
            raise exception
        except Exception as exception: # (want to catch all - at least for now) pylint: disable=broad-except
            error_message = f"Error Calculating Nowcast with a data_count of {data_count}, data_max is {data_max}, data_min is {data_min}, "
            error_message += f"weight_factor is {weight_factor}.\n"
            error_message += f"index is {i}, hours_ago is {hours_ago}, concentration is {concentrations[i]}\n"
            error_message += f"There are {len(timestamps)} with values of {timestamps}.\n"
            error_message += f"There are {len(concentrations)} with values of {concentrations}."
            self._logerr(error_message)
            raise CalculationError(error_message) from exception

    def calculate(self, db_manager, aqi_type, inputs):
        (timestamp, record_stats, records_iter) = inputs
        self._logdbg(f"The time stamp is {timestamp}.")
        self._logdbg(f"record_stats is {record_stats}.")
        self._logdbg(f"The type is '{aqi_type}'")

        data_count, data_min, data_max = record_stats

        records = list(records_iter)
        timestamps, concentrations = zip(*records)

        concentration = self.calculate_concentration(timestamp, data_count, data_min, data_max, timestamps, concentrations)
        aqi = self.sub_calculator.calculate(None, aqi_type, (concentration))
        self._logdbg(f"The computed AQI is {aqi}")

        return aqi

    def calculate_series(self, aqi_type, records_iter):
        ''' Calculate a series of nowcast aqi values. '''
        # 02/26/2025 - not used, yet (in development)
        self._logdbg(f"The type is '{aqi_type}'")

        i = 1
        timestamps = []
        concentrations = []
        min_concentration = float('inf')
        max_concentration = -float('inf')
        for record in records_iter:
            timestamps.append(record[0])
            concentrations.append(record[1])
            if record[1] < min_concentration:
                min_concentration = record[1]
            if record[1] > max_concentration:
                max_concentration = record[1]

            if i >= 11:
                break

            i += 1

        aqi_vec = []
        start_vec = []
        for record in records_iter:
            timestamps.append(record[0])
            concentrations.append(record[1])
            start_vec.append(timestamps[0])
            if record[1] < min_concentration:
                min_concentration = record[1]
            if record[1] > max_concentration:
                max_concentration = record[1]

            # ToDo: Research this if statement
            if concentrations[0] is not None:
                try:
                    concentration = self.calculate_concentration(timestamps[0],
                                                                 len(concentrations),
                                                                  min_concentration,
                                                                  max_concentration,
                                                                  timestamps,
                                                                  concentrations)
                    aqi = self.sub_calculator.calculate(None, aqi_type, (concentration))
                    aqi_vec.append(aqi)

                except weewx.CannotCalculate:
                    aqi_vec.append(None)
            else:
                aqi_vec.append(None)

            del timestamps[0]
            del concentrations[0]

        start_vec.reverse()
        stop_vec = start_vec[1:]
        stop_vec.append(start_vec[-1] + 3600)
        aqi_vec.reverse()

        return start_vec, stop_vec, aqi_vec

class EPAAQI(AbstractCalculator):
    """
    Class for calculating the EPA'S AQI.
    """

    aqi_bp = [
        # RGB = (R*65536)+(G*256)+B
        # Good: Green (0, 228, 0)
        {'min': 0, 'max': 50, 'color': f'{(0*65536)+(228*256)+0:06x}'},
        # Moderate: Yellow (255, 255, 0)
        {'min': 51, 'max': 100, 'color': f'{(255*65536)+(255*256)+0:06x}'},
        # Unhealthy for Sensitive Groups: Orange (255, 126, 0)
        {'min': 101, 'max': 150, 'color': f'{(255*65536)+(126*256)+0:06x}'},
        # Unhealthy: Red (255, 0, 0)
        {'min': 151, 'max': 200, 'color': f'{(255*65536)+(0*256)+0:06x}'},
        # Very Unhealthy: Purple (143, 63, 151)
        {'min': 201, 'max': 300, 'color': f'{(143*65536)+(63*256)+151:06x}'},
        # Hazardous: Maroon (126, 0, 35)
        {'min': 301, 'max': 500, 'color': f'{(126*65536)+(0*256)+35:06x}'},
    ]

    readings = {
        'pm2_5': {
            'prep_data': lambda x: math.trunc(x * 10) / 10,
            'breakpoints': [
                {'min': 0.0, 'max': 9.0},
                {'min': 9.1, 'max': 35.4},
                {'min': 35.5, 'max': 55.4},
                {'min': 55.5, 'max': 125.4},
                {'min': 125.5, 'max': 225.4},
                {'min': 225.5, 'max': 325.4},
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
                {'min': 425, 'max': 604},
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

    def calculate(self, db_manager, aqi_type, inputs):
        '''
        Calculate the AQI.
        Additional information:
          2024 Update:
            https://www.epa.gov/system/files/documents/2024-02/pm-naaqs-air-quality-index-fact-sheet.pdf
            https://document.airnow.gov/technical-assistance-document-for-the-reporting-of-daily-air-quailty.pdf
          Prior to 2024:
            https://www.airnow.gov/publications/air-quality-index/technical-assistance-document-for-reporting-the-daily-aqi/
            https://www.airnow.gov/aqi/aqi-calculator-concentration/
        '''

        (reading) = inputs
        try:
            self._logdbg(f"The input value is {reading}.")
            self._logdbg(f"The type is '{aqi_type}'")

            if reading is None:
                return reading

            readings = self.readings[aqi_type]

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

            aqi_bp_max = self.aqi_bp[index]['max']
            aqi_bp_min = self.aqi_bp[index]['min']

            self._logdbg(f"The AQI breakpoint index is {index},  max is {aqi_bp_max}, and the min is {aqi_bp_min}.")
            self._logdbg(f"The reading breakpoint max is {reading_bp_max:f} and the min is {reading_bp_min:f}.")

            aqi = round(((aqi_bp_max - aqi_bp_min)/(reading_bp_max - reading_bp_min) * (reading - reading_bp_min)) + aqi_bp_min)

            self._logdbg(f"The computed AQI is {aqi}")

            return aqi
        except Exception as exception: # (want to catch all - at least for now) pylint: disable=broad-except
            error_message = f"Error Calculating EPAAQI with a type of {aqi_type}, reading is {reading}, "
            error_message += "breakpoint_count is {breakpoint_count}.\n"
            error_message += f"The AQI breakpoint index is {index},  max is {aqi_bp_max}, and the min is {aqi_bp_min}.\n"
            error_message += f"The reading breakpoint max is {reading_bp_max:f} and the min is {reading_bp_min:f}."
            self._logerr(error_message)
            raise CalculationError(error_message) from exception

class EPAAQIDeprecatedV0(EPAAQI):
    """
    Class for calculating the EPA'S AQI.
    This is the algorithm (breakpoints) used to calculate the EPA AQI prior to 2024.
    Only the pm 2.5 breakpoint changed, but it was easier to just override the whole 'readings' data.
    In other words, the pm10 breakpoints are the same as the parent class, EPAAQI.
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
                field_option['get_scalar'] = self._get_scalar_nowcast
            else:
                if field_option['type'] not in EPAAQI.readings:
                    raise ValueError(f"Algorithm 'EPAAQI' is not supported for pollutant '{field_option['type']}'")
                field_option['support_aggregation'] = True
                field_option['support_series'] = True
                field_option['get_aggregate'] = self._get_aggregate_epaaqi
                field_option['get_series'] = self._get_series_epaaqi
                field_option['get_scalar'] = self._get_scalar_epaaqi
            field_option['calculator']  = \
                  getattr(sys.modules[__name__], field_option['algorithm'])(self.logger, log_level, sub_calculator, sub_field_name)

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

        aqi = self.aqi_fields[obs_type]['get_scalar'](obs_type, db_manager, record['dateTime'], record[dependent_field])

        unit_type, group = weewx.units.getStandardUnitType(record['usUnits'], obs_type)
        return weewx.units.ValueTuple(aqi, unit_type, group)

    def get_series(self, obs_type, timespan, db_manager, aggregate_type=None, aggregate_interval=None, **option_dict):
        """ Calculate the series. """
        if obs_type not in self.aqi_fields:
            raise weewx.UnknownType(obs_type)
        return self.aqi_fields[obs_type]['get_series'](obs_type, timespan, db_manager, aggregate_type, aggregate_interval, **option_dict)

    def get_aggregate(self, obs_type, timespan, aggregate_type, db_manager, **option_dict):
        """ Compute the aggregate. """
        if obs_type not in self.aqi_fields:
            raise weewx.UnknownType(obs_type)
        return self.aqi_fields[obs_type]['get_aggregate'](obs_type, timespan, aggregate_type, db_manager, **option_dict)

    def _get_scalar_nowcast(self, obs_type, db_manager, timestamp, _concentration):
        aqi_type = self.aqi_fields[obs_type]['type']
        dependent_field = self.aqi_fields[obs_type]["input"]

        if timestamp is None:
            raise weewx.CannotCalculate()

        timestamp_interval_start = weeutil.weeutil.startOfInterval(timestamp, 3600)
        stop = timestamp_interval_start + 3600
        start = stop - 43200
        record_stats = self.get_concentration_data_stats(db_manager, dependent_field, stop, start)
        records_iter = self.get_concentration_data_nowcast(db_manager, dependent_field, stop, start)

        try:
            aqi = self.aqi_fields[obs_type]['calculator'].calculate(db_manager, aqi_type, (timestamp, record_stats, records_iter))
        except weewx.CannotCalculate as exception:
            raise weewx.CannotCalculate(obs_type) from exception

        return aqi

    def _get_scalar_epaaqi(self, obs_type, db_manager, _timestamp, concentration):
        aqi_type = self.aqi_fields[obs_type]['type']

        try:
            aqi = self.aqi_fields[obs_type]['calculator'].calculate(db_manager, aqi_type, (concentration))
        except weewx.CannotCalculate as exception:
            raise weewx.CannotCalculate(obs_type) from exception

        return aqi

    def _get_series_nowcast(self, obs_type, _timespan, db_manager, aggregate_type, _aggregate_interval, **_option_dict):
        # For now the NOWCAST algorithm does not support 'series'
        # Because XTypeTable will also try, an empty 'set' of data is returned.
        unit, unit_group = weewx.units.getStandardUnitType(db_manager.std_unit_system, obs_type, aggregate_type)

        return (ValueTuple([], 'unix_epoch', 'group_time'),
                ValueTuple([], 'unix_epoch', 'group_time'),
                ValueTuple([], unit, unit_group))

    def _get_series_nowcast_prototype(self, obs_type, timespan, db_manager, aggregate_type, aggregate_interval, **_option_dict):
        aggregate_interval_seconds = weeutil.weeutil.nominal_spans(aggregate_interval)
        unit, unit_group = weewx.units.getStandardUnitType(db_manager.std_unit_system, obs_type, aggregate_type)

        # Because other XTypes will also try, an empty 'set' of data is returned.
        if timespan.stop - timespan.start < 3600:
            self._logerr("Series less than a hour are not supported.")
            return (ValueTuple([], 'unix_epoch', 'group_time'),
                    ValueTuple([], 'unix_epoch', 'group_time'),
                    ValueTuple([], unit, unit_group))
            #raise weewx.UnknownAggregation

        # Because other XTypes will also try, an empty 'set' of data is returned.
        # ToDo: placeholder
        if aggregate_type and aggregate_type not in ['min']:
            #raise weewx.UnknownAggregation
            self._logerr(f"Agregate type '{aggregate_type}' is not supported.")
            return (ValueTuple([], 'unix_epoch', 'group_time'),
                    ValueTuple([], 'unix_epoch', 'group_time'),
                    ValueTuple([], unit, unit_group))

        # Because other XTypes will also try, an empty 'set' of data is returned.
        # ToDo: what is valid?
        if aggregate_interval_seconds and aggregate_interval_seconds != 3600:
            #raise weewx.UnknownAggregation
            self._logerr(f"Agregate interval '{aggregate_interval}' is not supported.")
            #return (ValueTuple([], 'unix_epoch', 'group_time'),
            #        ValueTuple([], 'unix_epoch', 'group_time'),
            #        ValueTuple([], unit, unit_group))

        aqi_type = self.aqi_fields[obs_type]['type']
        dependent_field = self.aqi_fields[obs_type]["input"]
        stop = min(weeutil.weeutil.startOfInterval(time.time(), 3600), timespan.stop)
        # 'Need' 11 hours of data after current hour to compute nowcast qai
        start_time = timespan.start - 43200 + 3600
        records_iter = self.get_concentration_data_nowcast(db_manager, dependent_field, stop , start_time)

        start_list, stop_list, aqi_list = self.aqi_fields[obs_type]['calculator'].calculate_series(aqi_type, records_iter)

        # ToDo: placeholder
        if aggregate_type in ['min']:
            print("This is not supported")
            i = 0
            print(len(stop_list))

            list1 = []
            new_start_list = []
            new_stop_list = []
            new_concentration_list = []
            while i < len(stop_list):
                list1 = []
                start = stop_list[i]
                value_min = None
                value_min_time = None
                value_sum = 0
                while stop_list[i] < start + aggregate_interval_seconds:
                    value_sum += aqi_list[i]
                    if value_min is None:
                        value_min = aqi_list[i]
                        value_min_time = [start_list[i], stop_list[i]]
                    elif value_min < aqi_list[i]:
                        value_min = aqi_list[i]
                        value_min_time = (start_list[i], stop_list[i])

                    list1.append(stop_list[i])
                    i += 1
                    if len(stop_list) -1  < i:
                        break

                print(f" {i} {list1}")
                if aggregate_type == 'min':
                    new_start_list.append(value_min_time[0])
                    new_stop_list.append(value_min_time[1])
                    new_concentration_list.append(value_min)


        return (ValueTuple(start_list, 'unix_epoch', 'group_time'),
                ValueTuple(stop_list, 'unix_epoch', 'group_time'),
                ValueTuple(aqi_list, unit, unit_group))

    def _get_series_epaaqi(self, obs_type, timespan, db_manager, aggregate_type, aggregate_interval, **option_dict):
        aqi_type = self.aqi_fields[obs_type]['type']
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
            records_iter = self.get_concentration_data(obs_type, timespan, db_manager)

            for record in records_iter:
                aqi = None
                timestamp, unit_system, interval, input_value = record
                if std_unit_system:
                    if std_unit_system != unit_system:
                        raise weewx.UnsupportedFeature("Unit type cannot change within a time interval.")
                else:
                    std_unit_system = unit_system

                try:
                    aqi = self.aqi_fields[obs_type]['calculator'].calculate(db_manager, aqi_type, (input_value))
                except weewx.CannotCalculate:
                    aqi = None

                start_vec.append(timestamp - interval * 60)
                stop_vec.append(timestamp)
                data_vec.append(aqi)

            unit, unit_group = weewx.units.getStandardUnitType(std_unit_system, obs_type, aggregate_type)

        return (ValueTuple(start_vec, 'unix_epoch', 'group_time'),
                ValueTuple(stop_vec, 'unix_epoch', 'group_time'),
                ValueTuple(data_vec, unit, unit_group))

    def _get_aggregate_nowcast(self, obs_type, timespan, aggregate_type, db_manager, **_option_dict):
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
            simple_sql_stmts = {
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
            sql_stmt = simple_sql_stmts[aggregate_type].format(**interpolation_dict)

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

    def _get_aggregate_nowcast_prototype(self, obs_type, timespan, aggregate_type, db_manager, **_option_dict):
       # For now the NOWCAST algorithm does not support 'aggregation'
        # Because other XTypes will also try, 'None' is returned.
        # ToDo: example placeholder
        if timespan.stop - timespan.start < 86400:
            self._logerr("Aggregate intervals less than a day are not supported.")
            aggregate_value = None
            #raise weewx.UnknownAggregation
        elif aggregate_type == 'not_null':
            dependent_field = self.aqi_fields[obs_type]['input']

            interpolation_dict = {
                'start': timespan.start,
                'stop': timespan.stop,
                'table_name': db_manager.table_name,
                'input': dependent_field
            }

            # This is not accurate
            # Just because there is one concentration reading does not mean NOWCAST can be computed
            simple_sql_stmts = {
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
            sql_stmt = simple_sql_stmts[aggregate_type].format(**interpolation_dict)

            try:
                row = db_manager.getSql(sql_stmt)
            except weedb.NoColumnError:
                raise weewx.UnknownType(obs_type) from weedb.NoColumnError

            if not row or None in row:
                aggregate_value = None
            else:
                aggregate_value = row[0]
        elif aggregate_type == 'min':
            # ToDo: placeholder
            aqi_type = self.aqi_fields[obs_type]['type']
            _start_list, _stop_list, concentration_list =\
                self.aqi_fields[obs_type]['calculator'].calculate_series(aqi_type, 'foo')
            print(len(concentration_list))
            aggregate_value = None
        else:
            self._logerr(f"Agregate type '{aggregate_type}' is not supported.")
            aggregate_value = None
            # raise weewx.UnknownAggregation(aggregate_type)

        unit_type, group = weewx.units.getStandardUnitType(db_manager.std_unit_system, obs_type, aggregate_type)
        return weewx.units.ValueTuple(aggregate_value, unit_type, group)

    def _get_aggregate_epaaqi(self, obs_type, timespan, aggregate_type, db_manager, **_option_dict):
        aqi_type = self.aqi_fields[obs_type]['type']
        query_type, records_iter = self.get_aggregate_concentation_data(obs_type, timespan, aggregate_type, db_manager)

        if query_type == 'aggregate':
            input_values = []
            aggregate_value = None
            for row in records_iter:
                try:
                    input_value = self.aqi_fields[obs_type]['calculator'].calculate(db_manager, aqi_type, (row[0]))
                except weewx.CannotCalculate:
                    input_value = None

                if input_value is not None:
                    input_values.append(input_value)

            if input_values:
                aggregate_value = sum(input_values)
                if aggregate_type == 'avg':
                    aggregate_value = round(aggregate_value / len(input_values))
        else:
            row = list(records_iter)[0]

            if not row or None in row:
                input_value = None
            else:
                input_value = row[0]

            if query_type == 'simple':
                aggregate_value = input_value
            else:
                try:
                    aggregate_value = self.aqi_fields[obs_type]['calculator'].calculate(db_manager, aqi_type, (input_value))
                except weewx.CannotCalculate:
                    aggregate_value = None

        unit_type, group = weewx.units.getStandardUnitType(db_manager.std_unit_system, obs_type, aggregate_type)
        return weewx.units.ValueTuple(aggregate_value, unit_type, group)

    def get_concentration_data_stats(self, db_manager, dependent_field, stop, start):
        ''' Get the necessary concentration data to compute for a given time. '''

        # ToDo: need to get this from the 'console' (or the record?)
        archive_interval = 300

        stats_sql_str = f'''
        Select COUNT(rowStats.avgConcentration) as rowCount,
            MIN(rowStats.avgConcentration) as rowMin,
            MAX(rowStats.avgConcentration) as rowMax
        FROM (
            SELECT avg({dependent_field}) as avgConcentration
            FROM archive
            WHERE dateTime > {start}
                AND dateTime <= {stop}
            /* In WeeWX the first recording of an hour is the archival interval of the hour, typically 5 minutes.
            This interval records the values from 0 to 5 minutes
            In other words, assumning an archival interval of 5 minutes, the dateTimes will be
            05, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 00 (of the following hour)
            So, to get the correct grouping, the archive interval must deleted from dateTime in the database */
            GROUP BY (dateTime - {archive_interval}) / 3600
            ) AS rowStats
        '''

        try:
            # Only one record is returned
            record_stats = db_manager.getSql(stats_sql_str)
        except weedb.NoColumnError:
            raise weewx.UnknownType(dependent_field) from weedb.NoColumnError

        return record_stats

    def get_concentration_data_nowcast(self, db_manager, dependent_field, stop, start):
        ''' Get the necessary concentration data to compute for a given time. '''

        # ToDo: need to get this from the 'console'
        archive_interval = 300

        sql_str = f'''
        SELECT
            MAX(dateTime) - 3600,
            avg({dependent_field}) as avgConcentration
        FROM archive
        WHERE dateTime > {start}
            AND dateTime <= {stop}
        /* In WeeWX the first recording of an hour is the archival interval of the hour, typically 5 minutes.
        This interval records the values from 0 to 5 minutes
        In other words, assumning an archival interval of 5 minutes, the dateTimes will be
        05, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 00 (of the following hour)
        So, to get the correct grouping, the archive interval must deleted from dateTime in the database */
        GROUP BY (dateTime - {archive_interval}) / 3600
        ORDER BY dateTime DESC
        '''

        return db_manager.genSql(sql_str)

    def get_concentration_data(self, dependent_field, timespan, db_manager):
        ''' Get the concentration data necessary to compute AQI. '''
        dependent_field = self.aqi_fields[dependent_field]['input']
        sql_str = f'''
        SELECT 
            dateTime, 
            usUnits, 
            `interval`, 
            {dependent_field} 
        FROM 
            {db_manager.table_name} 
        WHERE dateTime > ? AND dateTime <= ?
        '''

        try:
            records_iter = db_manager.genSql(sql_str, timespan)
        except weedb.NoColumnError:
            raise weewx.UnknownType(dependent_field) from weedb.NoColumnError

        return records_iter

    def get_aggregate_concentation_data(self, obs_type, timespan, aggregate_type, db_manager):
        ''' Get the concentration data to compute aggregated AQI values. '''
        dependent_field = self.aqi_fields[obs_type]['input']

        simple_sql_stmts = {
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

        aggregate_sql_stmts = {
        'avg': "SELECT {input} FROM {table_name} "
               "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL",
        'sum': "SELECT {input} FROM {table_name} "
               "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL",
        }

        basic_sql_stmts = {
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
        sql_stmts = ChainMap(aggregate_sql_stmts, simple_sql_stmts, basic_sql_stmts)
        if aggregate_type not in sql_stmts:
            raise weewx.UnknownAggregation(aggregate_type)

        if aggregate_type in simple_sql_stmts:
            query_type = 'simple'
        elif aggregate_type in aggregate_sql_stmts:
            query_type = 'aggregate'
        else:
            query_type = 'basic'

        interpolation_dict = {
            'start': timespan.start,
            'stop': timespan.stop,
            'table_name': db_manager.table_name,
            'input': dependent_field
        }

        sql_stmt = sql_stmts[aggregate_type].format(**interpolation_dict)

        try:
            records_iter = db_manager.genSql(sql_stmt)
        except weedb.NoColumnError:
            raise weewx.UnknownType(obs_type) from weedb.NoColumnError

        return query_type, records_iter


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

# The following is to develop series support for nowcast
AQIType._get_series_nowcast = AQIType._get_series_nowcast_prototype # pylint: disable=protected-access
#AQIType._get_aggregate_nowcast = AQIType._get_aggregate_nowcast_prototype # pylint: disable=protected-access
