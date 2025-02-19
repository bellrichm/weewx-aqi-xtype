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

import user.aqitype

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

class TestEPAAQICalculate(unittest.TestCase):
    def test_get_scalar_valid_inputs(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        algorithm = 'EPAAQI'
        aqi_type = 'pm2_5'

        calculated_field = random_string()
        input_field = random_string()

        config_dict = setup_config(calculated_field, input_field, algorithm, aqi_type)
        config = configobj.ConfigObj(config_dict)

        aqi = random.randint(11, 100)
        with mock.patch.object(user.aqitype.EPAAQI, 'calculate', return_value=aqi):
            SUT = user.aqitype.AQIType(mock_logger, config)

            unit = random_string()
            unit_group = random_string()

            record = {
                'usUnits': 1,
                'interval': 5,
                'dateTime': time.time(),
                input_field: random.randint(0, 10),
            }

            with mock.patch('weewx.units.getStandardUnitType') as mock_get_standard_unit_type:
                mock_get_standard_unit_type.return_value = [unit, unit_group]

                value_tuple = SUT.get_scalar(calculated_field, record)

                self.assertEqual(value_tuple[0], aqi)
                self.assertEqual(value_tuple[1], unit)
                self.assertEqual(value_tuple[2], unit_group)

if __name__ == '__main__':
    #test_suite = unittest.TestSuite()
    #test_suite.addTest(TestEPAAQICalculate('test_get_scalar_valid_inputs'))
    #unittest.TextTestRunner().run(test_suite)

    unittest.main(exit=False)
