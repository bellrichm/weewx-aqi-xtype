#    Copyright (c) 2023 Rich Bell <bellrichm@gmail.com>
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

        self.assertEqual(calculator.calculate(None, None, 0.0, 'pm2_5'), 0)
        self.assertEqual(calculator.calculate(None, None, 5.0, 'pm2_5'), 28)
        self.assertEqual(calculator.calculate(None, None, 23.0, 'pm2_5'), 77)
        self.assertEqual(calculator.calculate(None, None, 40.0, 'pm2_5'), 112)
        self.assertEqual(calculator.calculate(None, None, 100.0, 'pm2_5'), 182)
        self.assertEqual(calculator.calculate(None, None, 200.0, 'pm2_5'), 275)
        self.assertEqual(calculator.calculate(None, None, 300.0, 'pm2_5'), 449)
        self.assertEqual(calculator.calculate(None, None, 400.0, 'pm2_5'), 649)
        self.assertEqual(calculator.calculate(None, None, 600.0, 'pm2_5'), 1047)
    def test_pm10_calculation(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        calculator = user.aqitype.EPAAQI(mock_logger, 0, None, None)

        self.assertEqual(calculator.calculate(None, None, 0.0, 'pm10'), 0)
        self.assertEqual(calculator.calculate(None, None, 25.0, 'pm10'), 23)
        self.assertEqual(calculator.calculate(None, None, 100.0, 'pm10'), 73)
        self.assertEqual(calculator.calculate(None, None, 200.0, 'pm10'), 123)
        self.assertEqual(calculator.calculate(None, None, 300.0, 'pm10'), 173)
        self.assertEqual(calculator.calculate(None, None, 400.0, 'pm10'), 266)
        self.assertEqual(calculator.calculate(None, None, 475.0, 'pm10'), 357)
        self.assertEqual(calculator.calculate(None, None, 550.0, 'pm10'), 440)
        self.assertEqual(calculator.calculate(None, None, 700.0, 'pm10'), 607)

if __name__ == '__main__':
    unittest.main(exit=False)
