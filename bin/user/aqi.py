#
#    Copyright (c) 2023 Rich Bell <bellrichm@gmail.com>
#
#    See the file LICENSE.txt for your full rights.
#
"""
WeeWX XTypes extensions that add new types of AQI.
"""

import math
import sys

from weewx.engine import StdService
import weewx.xtypes

class AQIService(StdService):
    """ A class to manage the registration of the AQI XType"""
    def __init__(self, engine, config_dict):
        super(AQIService, self).__init__(engine, config_dict)

        if 'aqi' not in config_dict:
            raise ValueError("[aqi] Needs to be configured")

        self.aqi = AQI(config_dict['aqi'])
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

        breakpoint_count = len(self.readings)
        index = 0
        while index < breakpoint_count:
            if reading < self.readings[aqi_type]['breakpoints'][index]['max']:
                break
            index += 1

        if index >= breakpoint_count:
            index = breakpoint_count

        reading_bp = self.readings[aqi_type]['breakpoints'][index]
        aqi_bp = self.aqi_bp[index]

        aqi = round((aqi_bp['max'] - aqi_bp['min'])/(reading_bp['max'] - reading_bp['min']) * \
              (reading - reading_bp['min']) + aqi_bp['min'])

        return aqi

class AQI(weewx.xtypes.XType):
    """
    AQI XType which computes the AQI (air quality index) from
    the pm2_5 value.
    """

    def __init__(self, config_dict):
        self.aqi_fields = config_dict

        for field in self.aqi_fields:
            self.aqi_fields[field]["calculator"]  = \
                  getattr(sys.modules[__name__], self.aqi_fields[field]['algorithm'])()

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
