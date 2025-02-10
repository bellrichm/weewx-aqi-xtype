#
#    Copyright (c) 2025 Rich Bell <bellrichm@gmail.com>
#
#    See the file LICENSE.txt for your full rights.
#

# This file is to see if there is any reasonable way to write tests for the AQIType class

import unittest
import mock

import configobj
import time

import user.aqitype

def setup_config():
    config_dict = {
        'pm2_5_aqi': {
            'input': 'pm2_5',
            'algorithm': 'EPAAQI',
            'type': 'pm2_5',
        }
    }

    return config_dict

class Test01(unittest.TestCase):
    @unittest.skip("Under development")
    def test01(self):
        print("test01:test01")
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        config_dict = setup_config()
        config = configobj.ConfigObj(config_dict)

        SUT = user.aqitype.AQIType(mock_logger, config)

        record = {
            'usUnits': 1,
            'interval': 5,
            'dateTime': time.time(),
            'pm2_5': 10,
        }

        aqi = SUT.get_scalar('pm2_5_aqi', record)
        print(aqi)

        print("test01:test01")

if __name__ == '__main__':
    test_suite = unittest.TestSuite()
    test_suite.addTest(Test01('test01'))
    unittest.TextTestRunner().run(test_suite)

    #unittest.main(exit=False)
