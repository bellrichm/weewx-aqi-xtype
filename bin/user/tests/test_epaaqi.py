#    Copyright (c) 2023-2025 Rich Bell <bellrichm@gmail.com>
#    See the file LICENSE.txt for your full rights.

# pylint: disable=missing-docstring

import random
import string
import unittest

import mock

import user.aqitype

def random_string(length=32):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(length)]) # pylint: disable=unused-variable

# https://www.airnow.gov/aqi/aqi-calculator/
class EPAAQITests(unittest.TestCase):
    def test_pm2_5_calculation(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        calculator = user.aqitype.EPAAQI(mock_logger, 0, None, None)

        self.assertEqual(calculator.calculate(None, 'pm2_5',  None, 0.0), 0)
        self.assertEqual(calculator.calculate(None, 'pm2_5',  None, 5.0), 28)
        self.assertEqual(calculator.calculate(None, 'pm2_5',  None, 23.0), 77)
        self.assertEqual(calculator.calculate(None, 'pm2_5',  None, 40.0), 112)
        self.assertEqual(calculator.calculate(None, 'pm2_5',  None, 100.0), 182)
        self.assertEqual(calculator.calculate(None, 'pm2_5',  None, 200.0), 275)
        self.assertEqual(calculator.calculate(None, 'pm2_5',  None, 300.0), 449)
        self.assertEqual(calculator.calculate(None, 'pm2_5',  None, 400.0), 649)
        self.assertEqual(calculator.calculate(None, 'pm2_5',  None, 600.0), 1047)

    def test_pm10_calculation(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        calculator = user.aqitype.EPAAQI(mock_logger, 0, None, None)

        self.assertEqual(calculator.calculate(None, 'pm10', None, 0.0), 0)
        self.assertEqual(calculator.calculate(None, 'pm10', None, 25.0), 23)
        self.assertEqual(calculator.calculate(None, 'pm10', None, 100.0), 73)
        self.assertEqual(calculator.calculate(None, 'pm10', None, 200.0), 123)
        self.assertEqual(calculator.calculate(None, 'pm10', None, 300.0), 173)
        self.assertEqual(calculator.calculate(None, 'pm10', None, 400.0), 266)
        self.assertEqual(calculator.calculate(None, 'pm10', None, 475.0), 357)
        self.assertEqual(calculator.calculate(None, 'pm10', None, 550.0), 440)
        self.assertEqual(calculator.calculate(None, 'pm10', None, 700.0), 607)

if __name__ == '__main__':
    unittest.main(exit=False)
