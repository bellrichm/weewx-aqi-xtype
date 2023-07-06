#
#    Copyright (c) 2023 Rich Bell <bellrichm@gmail.com>
#
#    See the file LICENSE.txt for your full rights.
#
"""
WeeWX XTypes extensions that add new types of AQI.
"""

import logging
import math
import sys

import weedb
from weewx.engine import StdService
from weewx.units import ValueTuple
import weewx.xtypes

log = logging.getLogger(__name__)

def logdbg(msg):
    """ log debug messages """
    log.debug(msg)

def loginf(msg):
    """ log informational messages """
    log.info(msg)

def logerr(msg):
    """ log error messages """
    log.error(msg)

VERSION = "1.0.0"

class AQITypeManager(StdService):
    """ A class to manage the registration of the AQI XType"""
    def __init__(self, engine, config_dict):
        super(AQITypeManager, self).__init__(engine, config_dict)

        if 'aqitype' not in config_dict:
            raise ValueError("[aqitype] Needs to be configured")

        loginf("Adding AQI type to the XTypes pipeline.")
        self.aqi = AQIType(config_dict['aqitype'])
        weewx.xtypes.xtypes.append(self.aqi)

    def shutDown(self):
        """Run when an engine shutdown is requested."""
        weewx.xtypes.xtypes.remove(self.aqi)

class EPAAQI(object):
    """
    Class for calculating the EPA'S AQI.
    """

    def __init__(self):
        self.readings = {
            "pm2_5": {
              "prep_data": lambda x: math.trunc(x * 10) / 10,
              "breakpoints": [
            {
                "min": 0.0,
                'max': 12.0,
            },
            {
                "min": 12.1,
                'max': 35.4,
            },
            {
                "min": 35.5,
                'max': 55.4,
            },
            {
                "min": 55.5,
                'max': 150.4,
            },
            {
                "min": 150.5,
                'max': 250.4,
            },
            {
                "min": 250.5,
                'max': 340.4,
            },
            {
                "min": 340.5,
                'max': 500.4,
            },
            ]},
            "pm10": {
                "prep_data": lambda x: math.trunc(x),
                "breakpoints": [
            {
                "min": 0.0,
                'max': 54,
            },
            {
                "min": 55,
                'max': 154,
            },
            {
                "min": 155,
                'max': 254,
            },
            {
                "min": 255,
                'max': 354,
            },
            {
                "min": 355,
                'max': 424,
            },
            {
                "min": 425,
                'max': 504,
            },
            {
                "min": 505,
                'max': 604,
            },
            ]}}

        self.aqi_bp = [
            {
                "min": 0,
                'max': 50,
            },
            {
                "min": 51,
                'max': 100,
            },
            {
                "min": 101,
                'max': 150,
            },
            {
                "min": 151,
                'max': 200,
            },
            {
                "min": 201,
                'max': 300,
            },
            {
                "min": 301,
                'max': 400,
            },
            {
                "min": 401,
                'max': 500,
            },
            ]

    def calculate(self, reading, aqi_type, obs_type):
        '''
        Calculate the AQI.
        '''

        if aqi_type not in self.readings:
            raise weewx.CannotCalculate(obs_type)

        readings = self.readings[aqi_type]

        breakpoint_count = len(readings['breakpoints'])
        index = 0
        while index < breakpoint_count:
            if reading < readings['breakpoints'][index]['max']:
                break
            index += 1

        if index >= breakpoint_count:
            index =  len(readings['breakpoints']) - 1

        reading_bp = readings['breakpoints'][index]
        aqi_bp = self.aqi_bp[index]

        aqi = round(((aqi_bp['max'] - aqi_bp['min'])/(reading_bp['max'] - reading_bp['min']) * \
              (reading - reading_bp['min'])) + aqi_bp['min'])

        return aqi

class AQIType(weewx.xtypes.XType):
    """
    AQI XType which computes the AQI (air quality index) from
    the pm2_5 value.
    """

    def __init__(self, config_dict):
        self.aqi_fields = config_dict

        for field in self.aqi_fields:
            self.aqi_fields[field]["calculator"]  = \
                  getattr(sys.modules[__name__], self.aqi_fields[field]['algorithm'])()

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
    }

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

        aqi = self.aqi_fields[obs_type]["calculator"].calculate(record[dependent_field],
                                                                aqi_type,
                                                                obs_type)

        unit_type, group = weewx.units.getStandardUnitType(record['usUnits'], obs_type)
        return weewx.units.ValueTuple(aqi, unit_type, group)

    def get_series(self, obs_type, timespan, db_manager, aggregate_type=None,
                   aggregate_interval=None,
                   **option_dict):

        if obs_type not in self.aqi_fields:
            raise weewx.UnknownType(obs_type)

        aqi_type = self.aqi_fields[obs_type]['type']

        dependent_field = self.aqi_fields[obs_type]["input"]

        start_vec = list()
        stop_vec = list()
        data_vec = list()

        if aggregate_type:
            return weewx.xtypes.ArchiveTable.get_series(obs_type, timespan, db_manager,
                                           aggregate_type, aggregate_interval, **option_dict)
        else:
            sql_str = 'SELECT dateTime, usUnits, `interval`, %s FROM %s ' \
                      'WHERE dateTime >= ? AND dateTime <= ? AND %s IS NOT NULL' \
                      % (dependent_field, db_manager.table_name, dependent_field)
            std_unit_system = None

            for record in db_manager.genSql(sql_str, timespan):
                timestamp, unit_system, interval, input_value = record
                if std_unit_system:
                    if std_unit_system != unit_system:
                        raise weewx.UnsupportedFeature(
                            "Unit type cannot change within a time interval.")
                else:
                    std_unit_system = unit_system

                    aqi = self.aqi_fields[obs_type]["calculator"].calculate(input_value,
                                                            aqi_type,
                                                            obs_type)

                start_vec.append(timestamp - interval * 60)
                stop_vec.append(timestamp)
                data_vec.append(aqi)

            unit, unit_group = weewx.units.getStandardUnitType(std_unit_system, obs_type,
                                                               aggregate_type)

        return (ValueTuple(start_vec, 'unix_epoch', 'group_time'),
                    ValueTuple(stop_vec, 'unix_epoch', 'group_time'),
                    ValueTuple(data_vec, unit, unit_group))

    def get_aggregate(self, obs_type, timespan, aggregate_type, db_manager, **option_dict):
        if obs_type not in self.aqi_fields:
            raise weewx.UnknownType(obs_type)

        if aggregate_type not in self.sql_stmts:
            raise weewx.UnknownAggregation(aggregate_type)

        dependent_field = self.aqi_fields[obs_type]["input"]
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
            aqi = self.aqi_fields[obs_type]["calculator"].calculate(input_value,
                                                    aqi_type,
                                                    obs_type)
        else:
            aqi = None

        unit_type, group = weewx.units.getStandardUnitType(db_manager.std_unit_system, obs_type,
                                               aggregate_type)

        return weewx.units.ValueTuple(aqi, unit_type, group)
