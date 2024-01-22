#    Copyright (c) 2023-2024 Rich Bell <bellrichm@gmail.com>
#    See the file LICENSE.txt for your full rights.

"""
WeeWX XTypes extensions that add new types of AQI.
"""

import logging
import math
import sys

import weedb
import weeutil
import weewx
import weewx.cheetahgenerator
from weewx.engine import StdService
from weewx.units import ValueTuple
from weeutil.weeutil import to_int

VERSION = '1.1.1-rc02'

class Logger(object):
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
        super(AQITypeManager, self).__init__(engine, config_dict)

        self.logger = Logger()

        if 'aqitype' not in config_dict:
            raise ValueError("[aqitype] Needs to be configured")

        self._setup(config_dict['aqitype'])

        self.logger.loginf("Adding AQI type to the XTypes pipeline.")
        self.aqi = AQIType(self.logger, config_dict['aqitype'])
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
            self.logger.logdbg("(NOWCAST) %s" % msg)

    def _loginf(self, msg):
        if self.log_level <= 20:
            self.logger.loginf("(NOWCAST) %s" % msg)

    def _logerr(self, msg):
        if self.log_level <= 40:
            self.logger.logerr("(NOWCAST) %s" % msg)

    def calculate_concentration(self, db_manager, time_stamp):
        '''
        Calculate the nowcast concentration.
        '''
        current_hour = weeutil.weeutil.startOfInterval(time_stamp, 3600)
        two_hours_ago = current_hour - 7200
        xtype = weewx.xtypes.ArchiveTable()

        _, stop_vec, data = xtype.get_series(self.sub_field_name,
                                                    weeutil.weeutil.TimeSpan((current_hour - 43200), current_hour),
                                                    db_manager, aggregate_type='avg',
                                                    aggregate_interval=3600)
        
        self._logdbg(f"The data returned is {data[0]}.")
        self._logdbg(f"The timestamps returned is {stop_vec[0]}.")

        min_value = None
        max_value = None
        index = len(data[0]) - 1
        while index >= 0 :
            if data[0][index] is None:
                del data[0][index]
                del stop_vec[0][index]
            else:
                if min_value is None or data[0][index] < min_value:
                    min_value = data[0][index]

                if max_value is None or data[0][index] > max_value:
                    max_value = data[0][index]
            index -= 1

        data_count = len(stop_vec[0])
        self._logdbg("Number of readings are: %s" % data_count)

        self._logdbg(f"The data after filtering is {data[0]}.")
        self._logdbg(f"The timestamps after filtering is {stop_vec[0]}.")

        if data_count < 2:
            raise weewx.CannotCalculate

        if data_count == 2 and stop_vec[0][0] < two_hours_ago:
            self._logdbg("Not enough recent readings.")
            raise weewx.CannotCalculate

        if stop_vec[0][data_count - 3] < two_hours_ago:
            self._logdbg("Not enough recent readings.")
            raise weewx.CannotCalculate

        data_range = max_value - min_value
        scaled_rate_change = data_range/max_value
        weight_factor = max((1-scaled_rate_change), .5)
        numerator = 0
        denominator = 0
        i = 0
        while i < data_count:
            hours_ago = ((current_hour - stop_vec[0][i]) / 3600)
            self._logdbg("Hours ago: %s pm was: %s" % (hours_ago, data[0][i]))
            numerator += data[0][i] * (weight_factor ** hours_ago)
            denominator += weight_factor ** hours_ago
            i += 1

        concentration = math.trunc((numerator / denominator) * 10) / 10
        self._logdbg("The computed concentration is %s" % concentration)
        return concentration

    def calculate(self, db_manager, time_stamp, reading, aqi_type):
        self._logdbg("The time stamp is %s." % time_stamp)
        self._logdbg("The type is '%s'" % aqi_type)

        if time_stamp is None:
            raise weewx.CannotCalculate()

        if aqi_type not in NOWCAST.readings:
            raise weewx.CannotCalculate()

        concentration = self.calculate_concentration(db_manager, time_stamp)
        aqi = self.sub_calculator.calculate(None, None, concentration, aqi_type)
        self._logdbg("The computed AQI is %s" % aqi)

        return aqi

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
            self.logger.logdbg("(EPAAQI) %s" % msg)

    def _loginf(self, msg):
        if self.log_level <= 20:
            self.logger.loginf("(EPAAQI) %s" % msg)

    def _logerr(self, msg):
        if self.log_level <= 40:
            self.logger.logerr("(EPAAQI) %s" % msg)

    def calculate(self, db_manager, time_stamp, reading, aqi_type):
        '''
        Calculate the AQI.
        Additional information:
        https://www.airnow.gov/publications/air-quality-index/technical-assistance-document-for-reporting-the-daily-aqi/
        https://www.airnow.gov/aqi/aqi-calculator-concentration/
        '''

        self._logdbg("The input value is %f." % reading)
        self._logdbg("The type is '%s'" % aqi_type)

        if aqi_type not in EPAAQI.readings:
            raise weewx.CannotCalculate()

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

        self._logdbg("The AQI breakpoint index is %i,  max is %i, and the min is %i." % (index, aqi_bp_max, aqi_bp_min))
        self._logdbg("The reading breakpoint max is %f and the min is %f." % (reading_bp_max, reading_bp_min))

        aqi = round(((aqi_bp_max - aqi_bp_min)/(reading_bp_max - reading_bp_min) * (reading - reading_bp_min)) + aqi_bp_min)

        self._logdbg("The computed AQI is %s" % aqi)

        return aqi

class AQIType(weewx.xtypes.XType):
    """
    AQI XType which computes the AQI (air quality index) from
    the pm2_5 value.
    """

    def __init__(self, logger, config_dict):
        self.logger = logger
        self.aqi_fields = config_dict
        default_log_level = config_dict.get('log_level', 20)

        for field in self.aqi_fields:
            sub_calculator = None
            sub_field_name = None
            log_level = to_int(self.aqi_fields[field].get('log_level', default_log_level))
            if self.aqi_fields[field]['algorithm'] == 'NOWCAST':
                self.aqi_fields[field]['support_aggregation'] = False
                self.aqi_fields[field]['support_series'] = False
                sub_calculator = getattr(sys.modules[__name__], 'EPAAQI')(self.logger, log_level, None, None)
                sub_field_name = self.aqi_fields[field]['input']
            else:
                self.aqi_fields[field]['support_aggregation'] = True
                self.aqi_fields[field]['support_series'] = True
            self.aqi_fields[field]['calculator']  = \
                  getattr(sys.modules[__name__], self.aqi_fields[field]['algorithm'])(self.logger, log_level, sub_calculator, sub_field_name)

        self.sql_stmts = {
        'avg': "SELECT AVG({input}) FROM {table_name} "
               "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL",
        'count': "SELECT COUNT(dateTime) FROM {table_name} "
                 "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL",
        'first': "SELECT {input} FROM {table_name} "
                 "WHERE dateTime = (SELECT MIN(dateTime) FROM {table_name} "
                 "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL",
        'last': "SELECT {input} FROM {table_name} "
                "WHERE dateTime = (SELECT MAX(dateTime) FROM {table_name} "
                "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL",
        'min': "SELECT {input} FROM {table_name} "
               "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL "
               "ORDER BY {input} ASC LIMIT 1;",
        'max': "SELECT {input} FROM {table_name} "
               "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL "
               "ORDER BY {input} DESC LIMIT 1;",
        'sum': "SELECT SUM({input}) FROM {table_name} "
               "WHERE dateTime > {start} AND dateTime <= {stop} AND {input} IS NOT NULL)",
        'not_null': "SELECT 1 FROM {table_name} "
                    "WHERE dateTime > {start} AND dateTime <= {stop} "
                    "AND {input} IS NOT NULL LIMIT 1",
    }

    def _logdbg(self, msg):
        self.logger.logdbg("(XTYPE) %s" % msg)

    def _loginf(self, msg):
        self.logger.loginf("(XTYPE) %s" % msg)

    def _logerr(self, msg):
        self.logger.logerr("(XTYPE) %s" % msg)

    def get_scalar(self, obs_type, record, db_manager=None, **option_dict):
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

        if obs_type not in self.aqi_fields:
            raise weewx.UnknownType(obs_type)

        aqi_type = self.aqi_fields[obs_type]['type']

        dependent_field = self.aqi_fields[obs_type]['input']

        start_vec = list()
        stop_vec = list()
        data_vec = list()

        if aggregate_type:
            return weewx.xtypes.ArchiveTable.get_series(obs_type, timespan, db_manager, aggregate_type, aggregate_interval, **option_dict)
        else:
            sql_str = 'SELECT dateTime, usUnits, `interval`, %s FROM %s ' \
                      'WHERE dateTime >= ? AND dateTime <= ? AND %s IS NOT NULL' \
                      % (dependent_field, db_manager.table_name, dependent_field)
            std_unit_system = None

            for record in db_manager.genSql(sql_str, timespan):
                timestamp, unit_system, interval, input_value = record
                if std_unit_system:
                    if std_unit_system != unit_system:
                        raise weewx.UnsupportedFeature("Unit type cannot change within a time interval.")
                else:
                    std_unit_system = unit_system

                    try:
                        aqi = self.aqi_fields[obs_type]['calculator'].calculate(db_manager, None, input_value, aqi_type)
                    except weewx.CannotCalculate as exception:
                        raise weewx.CannotCalculate(obs_type) from exception

                start_vec.append(timestamp - interval * 60)
                stop_vec.append(timestamp)
                data_vec.append(aqi)

            unit, unit_group = weewx.units.getStandardUnitType(std_unit_system, obs_type, aggregate_type)

        return (ValueTuple(start_vec, 'unix_epoch', 'group_time'),
                ValueTuple(stop_vec, 'unix_epoch', 'group_time'),
                ValueTuple(data_vec, unit, unit_group))

    def get_aggregate(self, obs_type, timespan, aggregate_type, db_manager, **option_dict):
        if obs_type not in self.aqi_fields:
            raise weewx.UnknownType(obs_type)

        if aggregate_type not in self.sql_stmts:
            raise weewx.UnknownAggregation(aggregate_type)

        dependent_field = self.aqi_fields[obs_type]['input']
        aqi_type = self.aqi_fields[obs_type]['type']

        interpolation_dict = {
            'start': timespan.start,
            'stop': timespan.stop,
            'table_name': db_manager.table_name,
            'input': dependent_field
        }

        sql_stmt = self.sql_stmts[aggregate_type].format(**interpolation_dict)

        try:
            row = db_manager.getSql(sql_stmt)
        except weedb.NoColumnError:
            raise weewx.UnknownType(obs_type)

        if not row or None in row:
            input_value = None
        else:
            input_value = row[0]

        if input_value is not None:
            try:
                aqi = self.aqi_fields[obs_type]['calculator'].calculate(db_manager, None, input_value, aqi_type)
            except weewx.CannotCalculate as exception:
                raise weewx.CannotCalculate(obs_type) from exception

        else:
            aqi = None

        unit_type, group = weewx.units.getStandardUnitType(db_manager.std_unit_system, obs_type, aggregate_type)

        return weewx.units.ValueTuple(aqi, unit_type, group)

class AQISearchList(weewx.cheetahgenerator.SearchList):
    """ Implement tags used by templates in the skin. """
    def __init__(self, generator):
        weewx.cheetahgenerator.SearchList.__init__(self, generator)

        self.logger = Logger()

    def get_extension_list(self, timespan, db_lookup):
        search_list_extension = {'AQIColor': self.get_aqi_color,
                                 'AQIDescription': self.get_aqi_description,
                                 'logdbg': self._logdbg,
                                 'loginf': self._loginf,
                                 'logerr': self._logerr,
                                 'version': VERSION,
                                }

        return [search_list_extension]

    def _logdbg(self, msg):
        self.logger.logdbg("(SLE) %s" % msg)

    def _loginf(self, msg):
        self.logger.loginf("(SLE) %s" % msg)

    def _logerr(self, msg):
        self.logger.logerr("(SLE) %s" % msg)

    def get_aqi_color(self, value, standard):
        """ Given an AQI value and standard, return the corresponding color"""
        aqi_bp = getattr(sys.modules[__name__], standard).aqi_bp
        index = self._get_index(aqi_bp, value)

        return aqi_bp[index]['color']

    def get_aqi_description(self, value, standard):
        """ Given an AQI value and standard, return the corresponding description"""
        aqi_bp = getattr(sys.modules[__name__], standard).aqi_bp
        level = self._get_index(aqi_bp, value) + 1

        return "aqi_%s_description%i"  % (standard, level)

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
    