#
#    Copyright (c) 2025 Rich Bell <bellrichm@gmail.com>
#
#    See the file LICENSE.txt for your full rights.
#

# pylint: disable=wrong-import-order
# pylint: disable=missing-docstring

# ToDo: This is a start of a way to test SQL statements.
# This tests getting data from the database to calcuate the NOWCAST value.

import unittest
import mock

import configobj
import io
import random
import string

import weewx.manager

import user.aqitype

CONFIG_DICT = '''
WEEWX_ROOT = 'bin/user/tests/'

#   This section binds a data store to a database.
[DataBindings]
    [[aqi_binding]]
        database = aqi
        table_name = archive
        manager = weewx.wxmanager.WXDaySummaryManager
        schema = schemas.wview_extended.schema
    
#   This section defines various databases.
[Databases]
    [[aqi]]
        database_name = pm.sdb
        database_type = SQLite

#   This section defines defaults for the different types of databases.
[DatabaseTypes]
    [[SQLite]]
        driver = weedb.sqlite
        SQLITE_ROOT = data
        '''

def random_string(length=32):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(length)]) # pylint: disable=unused-variable

class Test01(unittest.TestCase):
    def test_01(self):
        mock_logger = mock.Mock(spec=user.aqitype.Logger)

        config = configobj.ConfigObj(io.StringIO(CONFIG_DICT))
        db_binder = weewx.manager.DBBinder(config)
        db_manager = db_binder.get_manager('aqi_binding')

        SUT = user.aqitype.NOWCAST(mock_logger, random.randint(1, 100), random_string(), 'pm2_5')

        # The timestamp in the template that I am using is 1740168300 (3:05 PM Eastern on 2/21/2025)
        # The code finds the hour that this timestamp belongs to, it is 1740168000 (3:00 PM Eastern on 2/21/2025)
        # This is the stop value that is passed into _get_concentration_data
        # This is used as the stop value in the SQL queries
        ret_value = SUT._get_concentration_data(db_manager, 1740168000)

        self.assertEqual(ret_value,
                         (12, 1.1982950191570885, 1.7157567049808427,
                          (1740171300, 1740168000, 1740164400, 1740160800, 1740157200, 1740153600, 1740150000, 1740146400, 1740142800, 1740139200, 1740135600, 1740132000),
                          (1.3857366771159874, 1.4406226053639848, 1.5153544061302677, 1.7157567049808427, 1.4154310344827585, 1.5376532567049808, 1.3357950191570878, 1.5952873563218388, 1.3942241379310343, 1.4037739463601533, 1.1982950191570885, 1.2343007662835248)
                         )
)

        db_binder.close()

if __name__ == '__main__':
    test_suite = unittest.TestSuite()
    test_suite.addTest(Test01('test_01'))
    unittest.TextTestRunner().run(test_suite)

    #unittest.main(exit=False)
