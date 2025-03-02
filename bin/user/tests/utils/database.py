'''
Necessary data and functions to initialize a WeeWX database to be used for testing SQL statements.
'''
#
#    Copyright (c) 2025 Rich Bell <bellrichm@gmail.com>
#
#    See the file LICENSE.txt for your full rights.
#

import random
import string

import weewx.manager
import weeutil.weeutil

from utils import data

def random_string(length=32):
    ''' Create a random string. '''
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(length)])  # pylint: disable=unused-variable

PM2_5_INPUT_FIELD = random_string(5)

US_UNITS = 1
ARCHIVE_INTERVAL_MINUTES = 5
ARCHIVE_INTERVAL_SECONDS = ARCHIVE_INTERVAL_MINUTES * 60

timespan = weeutil.weeutil.TimeSpan(
    data.db_20250221_timestamps[0] - ARCHIVE_INTERVAL_SECONDS, data.db_20250221_timestamps[-1])


def _generate_records(pm2_5_column):
    ''' Generate records to be inserted into a WeeWX database. '''
    i = 0
    for date_time in data.db_20250221_timestamps:
        yield {
            'dateTime': date_time,
            'usUnits': US_UNITS,
            'interval': ARCHIVE_INTERVAL_MINUTES,
            pm2_5_column: data.db_20250221_pm2_5_values[i],
        }
        i += 1


def get_db_manager(pm2_5_column):
    ''' Create a WeeWX database and initialize its db manager. '''

    table = [('dateTime', 'INTEGER NOT NULL UNIQUE PRIMARY KEY'),
             ('usUnits', 'INTEGER NOT NULL'),
             ('interval', 'INTEGER NOT NULL'),
             (pm2_5_column, 'REAL'),
             ]

    day_summaries = [(e[0], 'scalar') for e in table
                     if e[0] not in ('dateTime', 'usUnits', 'interval')]

    schema = {
        'table': table,
        'day_summaries': day_summaries
    }

    db_manager = weewx.manager.Manager.open_with_create(
        {
            'database_name': ':memory:',
            'driver': 'weedb.sqlite'
        },
        schema=schema)

    for record in _generate_records(pm2_5_column):
        db_manager.addRecord(record)

    return db_manager


def backup(db_manager, filename):
    ''' Create a backup of the database being managed by db_manager to the file named filename. '''
    import sqlite3  # want to ensure that sqlite3 use is limited, pylint: disable=import-outside-toplevel

    backup_connection = sqlite3.connect(filename)
    db_manager.connection.connection.backup(backup_connection)
    backup_connection.close()
