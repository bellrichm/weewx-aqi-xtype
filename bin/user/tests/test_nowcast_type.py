#    Copyright (c) 2025 Rich Bell <bellrichm@gmail.com>
#
#    See the file LICENSE.txt for your full rights.
#

# pylint: disable=wrong-import-order
# pylint: disable=missing-docstring
# pylint: disable=invalid-name

import unittest
import mock

import random

import user.aqitype

import utils.database

class TestNowcastDevelopment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input_field = utils.database.PM2_5_INPUT_FIELD
        cls.db_manager = utils.database.get_db_manager(cls.input_field)

        # Create a backup of the database used in these tests.
        # This could be useful if there is a problem in the tests.
        utils.database.backup(cls.db_manager, 'bin/user/tests/utils/test_nowcast_calculate.sdb')

    @classmethod
    def tearDownClass(cls):
        cls.db_manager.close()
        cls.db_manager = None

    def setUp(self):
        self.mock_logger = mock.Mock(spec=user.aqitype.Logger)

    @unittest.skip('ToDo: needs updating')
    def test_calculate_series_prototype(self):
        # ToDo: This 'test' will be used to develop series support for the Nowcast algorithm.
        #       Note, due to performance concerns, I am not sure the Nowcast algotithm will be supported.
        #
        sub_calculator = user.aqitype.EPAAQI(self.mock_logger, random.randint(1, 100), None, None)
        SUT = user.aqitype.NOWCAST(self.mock_logger, random.randint(1, 100), sub_calculator, TestNowcastDevelopment.input_field)

        start_vec, stop_vec, aqi_vec = SUT.calculate_series('pm2_5', 'foo')

        self.assertEqual(start_vec,
                         [1740114000, 1740117600, 1740121200, 1740124800, 1740128400, 1740132000,
                          1740135600, 1740139200, 1740142800, 1740146400, 1740150000, 1740153600,
                          1740157200, 1740160800, 1740164400, 1740168000, 1740171600, 1740175200,
                          1740178800, 1740182400, 1740186000, 1740189600, 1740193200, 1740196800])
        self.assertEqual(stop_vec,
                         [1740117600, 1740121200, 1740124800, 1740128400, 1740132000, 1740135600,
                          1740139200, 1740142800, 1740146400, 1740150000, 1740153600, 1740157200,
                          1740160800, 1740164400, 1740168000, 1740171600, 1740175200, 1740178800,
                          1740182400, 1740186000, 1740189600, 1740193200, 1740196800, 1740200400])
        self.assertEqual(aqi_vec,
                         [9, 8, 7, 8, 7, 7,7, 7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 7, 7, 7, 7, 7, 7, 8])

if __name__ == '__main__':

    unittest.main(exit=False)
