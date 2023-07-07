
# pylint: disable=missing-docstring

import unittest
import mock

import user.aqitype

class EPAAQITests(unittest.TestCase):

    def test_first_breakpoint(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)
        calculator = user.aqitype.EPAAQI(mock_logger)

        self.assertEqual(calculator.calculate(5.0, 'pm2_5'), 21)

if __name__ == '__main__':
    unittest.main(exit=False)
