
# pylint: disable=missing-docstring

import unittest
import mock

import user.aqitype

class EPAAQITests(unittest.TestCase):

    def test_pm2_5_calculation(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        calculator = user.aqitype.EPAAQI(mock_logger)

        
        self.assertEqual(calculator.calculate(0.0, 'pm2_5'), 0)
        self.assertEqual(calculator.calculate(5.0, 'pm2_5'), 21)
        self.assertEqual(calculator.calculate(23.0, 'pm2_5'), 74)
        self.assertEqual(calculator.calculate(40.0, 'pm2_5'), 112)
        self.assertEqual(calculator.calculate(100.0, 'pm2_5'), 174)
        self.assertEqual(calculator.calculate(200.0, 'pm2_5'), 250)
        self.assertEqual(calculator.calculate(300.0, 'pm2_5'), 350)
        self.assertEqual(calculator.calculate(400.0, 'pm2_5'), 434) 
        self.assertEqual(calculator.calculate(600.0, 'pm2_5'), 566)


if __name__ == '__main__':
    unittest.main(exit=False)
