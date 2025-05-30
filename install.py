#    Copyright (c) 2023-2025 Rich Bell <bellrichm@gmail.com>
#    See the file LICENSE.txt for your rights.

""" Installer for the AQI XType. """

from io import StringIO

import configobj
from weecfg.extension import ExtensionInstaller

VERSION = "2.0.0-rc05"

EXTENSION_CONFIG = """
[StdReport]
    [[Defaults]]
        [[[Labels]]]
            [[[[Generic]]]]
                pm2_5_aqi = AQI
                pm2_5_aqi_nowcast = AQI (NowCast)

[StdWXCalculate]
    [[Calculations]]
        pm2_5_aqi = prefer_hardware
        # Since this requires a database look up, by default do not populate loop packets
        pm2_5_aqi_nowcast = prefer_hardware, archive

[aqitype]
    # The name of AQI field.
    # Create a section for each field to be calculated.
    [[pm2_5_aqi]]
        # The name of the WeeWX observation to be used in the calculation.
        input = pm2_5
        # The name of the algorithm.
        # Supported values: EPAAQI, NowCast
        algorithm = EPAAQI
        # If the algorithm supports different pollutants(pm 2.5, pm 10, etc)
        # Supported values: pm2_5, pm10
        type = pm2_5      
    [[pm2_5_aqi_nowcast]]
        # The name of the WeeWX observation to be used in the calculation.
        input = pm2_5
        # The name of the algorithm.
        # Supported values: EPAAQI, NowCast
        algorithm = NowCast
        # If the algorithm supports different pollutants(pm 2.5, pm 10, etc)
        # Supported values: pm2_5, pm10
        type = pm2_5                          
"""

EXTENSION_DICT = configobj.ConfigObj(StringIO(EXTENSION_CONFIG))

def loader():
    """ Load and return the extension installer. """
    return AQITypeInstaller()

class AQITypeInstaller(ExtensionInstaller):
    """ The extension installer. """

    def __init__(self):
        super(AQITypeInstaller, self).__init__(
            version=VERSION,
            name='AQITYPE',
            description='Dynamically compute AQI via WeeWX Xtype.',
            author="Rich Bell",
            author_email="bellrichm@gmail.com",
            xtype_services='user.aqitype.AQITypeManager',
            config=EXTENSION_DICT,
            files=[('bin/user', ['bin/user/aqitype.py']),
                   ]
        )
