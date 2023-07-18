#    Copyright (c) 2023 Rich Bell <bellrichm@gmail.com>
#    See the file LICENSE.txt for your full rights.

# pylint: disable=missing-docstring

import random
import string
import unittest

import mock

import user.aqitype
import weewx

def random_string(length=32):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(length)]) # pylint: disable=unused-variable

class EPAAQITests(unittest.TestCase):

    def test_invalid_type(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        calculator = user.aqitype.EPAAQI(mock_logger, None, None)

        with self.assertRaises(weewx.CannotCalculate):
            calculator.calculate(None, None, random.uniform(0, 700), random_string())

    def test_pm2_5_calculation(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        calculator = user.aqitype.EPAAQI(mock_logger, None, None)

        self.assertEqual(calculator.calculate(None, None, 0.0, 'pm2_5'), 0)
        self.assertEqual(calculator.calculate(None, None, 5.0, 'pm2_5'), 21)
        self.assertEqual(calculator.calculate(None, None, 23.0, 'pm2_5'), 74)
        self.assertEqual(calculator.calculate(None, None, 40.0, 'pm2_5'), 112)
        self.assertEqual(calculator.calculate(None, None, 100.0, 'pm2_5'), 174)
        self.assertEqual(calculator.calculate(None, None, 200.0, 'pm2_5'), 250)
        self.assertEqual(calculator.calculate(None, None, 300.0, 'pm2_5'), 350)
        self.assertEqual(calculator.calculate(None, None, 400.0, 'pm2_5'), 434)
        self.assertEqual(calculator.calculate(None, None, 600.0, 'pm2_5'), 566)

    def test_pm10_calculation(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        calculator = user.aqitype.EPAAQI(mock_logger, None, None)

        self.assertEqual(calculator.calculate(None, None, 0.0, 'pm10'), 0)
        self.assertEqual(calculator.calculate(None, None, 25.0, 'pm10'), 23)
        self.assertEqual(calculator.calculate(None, None, 100.0, 'pm10'), 73)
        self.assertEqual(calculator.calculate(None, None, 200.0, 'pm10'), 123)
        self.assertEqual(calculator.calculate(None, None, 300.0, 'pm10'), 173)
        self.assertEqual(calculator.calculate(None, None, 400.0, 'pm10'), 266)
        self.assertEqual(calculator.calculate(None, None, 475.0, 'pm10'), 364)
        self.assertEqual(calculator.calculate(None, None, 550.0, 'pm10'), 446)
        self.assertEqual(calculator.calculate(None, None, 700.0, 'pm10'), 596)

if __name__ == '__main__':
    unittest.main(exit=False)
