#    Copyright (c) 2025 Rich Bell <bellrichm@gmail.com>
#    See the file LICENSE.txt for your full rights.

# pylint: disable=missing-docstring

import random
import string
import unittest

import mock

import user.aqitype

def random_string(length=32):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(length)]) # pylint: disable=unused-variable

class EPAAQITests(unittest.TestCase):
    def test_pm2_5_calculation(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        calculator = user.aqitype.EPAAQIDeprecatedV0(mock_logger, 0, None, None)

        self.assertEqual(calculator.calculate(None, 'pm2_5', (0.0)), 0)
        self.assertEqual(calculator.calculate(None, 'pm2_5', (5.0)), 21)
        self.assertEqual(calculator.calculate(None, 'pm2_5', (23.0)), 74)
        self.assertEqual(calculator.calculate(None, 'pm2_5', (40.0)), 112)
        self.assertEqual(calculator.calculate(None, 'pm2_5', (100.0)), 174)
        self.assertEqual(calculator.calculate(None, 'pm2_5', (200.0)), 250)
        self.assertEqual(calculator.calculate(None, 'pm2_5', (300.0)), 350)
        self.assertEqual(calculator.calculate(None, 'pm2_5', (400.0)), 434)
        self.assertEqual(calculator.calculate(None, 'pm2_5', (600.0)), 566)

    def test_pm10_calculation(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        calculator = user.aqitype.EPAAQIDeprecatedV0(mock_logger, 0, None, None)

        self.assertEqual(calculator.calculate(None, 'pm10', (0.0)), 0)
        self.assertEqual(calculator.calculate(None, 'pm10', (25.0)), 23)
        self.assertEqual(calculator.calculate(None, 'pm10', (100.0)), 73)
        self.assertEqual(calculator.calculate(None, 'pm10', (200.0)), 123)
        self.assertEqual(calculator.calculate(None, 'pm10', (300.0)), 173)
        self.assertEqual(calculator.calculate(None, 'pm10', (400.0)), 266)
        self.assertEqual(calculator.calculate(None, 'pm10', (475.0)), 364)
        self.assertEqual(calculator.calculate(None, 'pm10', (550.0)), 446)
        self.assertEqual(calculator.calculate(None, 'pm10', (700.0)), 596)

if __name__ == '__main__':
    unittest.main(exit=False)
