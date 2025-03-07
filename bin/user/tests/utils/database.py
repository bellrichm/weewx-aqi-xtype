#
#    Copyright (c) 2025 Rich Bell <bellrichm@gmail.com>
#
#    See the file LICENSE.txt for your full rights.
#

'''
Necessary functions to initialize a WeeWX database to be used for testing SQL statements.
'''

import weewx.manager
import weeutil.weeutil

import data
import helpers

PM2_5_INPUT_FIELD = helpers.random_string(5)

US_UNITS = 1
ARCHIVE_INTERVAL_MINUTES = 5
ARCHIVE_INTERVAL_SECONDS = ARCHIVE_INTERVAL_MINUTES * 60

timespan = weeutil.weeutil.TimeSpan(
    data.db_20250221_timestamps[0] - ARCHIVE_INTERVAL_SECONDS, data.db_20250221_timestamps[-1])


def _generate_records(pm2_5_column):
    ''' Generate records to be inserted into a WeeWX database. '''
    pm2_5_values =  data.db_20250220_pm2_5_values + data.db_20250221_pm2_5_values
    timestamps = data.db_20250220_timestamps + data.db_20250221_timestamps
    i = 0
    for date_time in timestamps:
        yield {
            'dateTime': date_time,
            'usUnits': US_UNITS,
            'interval': ARCHIVE_INTERVAL_MINUTES,
            pm2_5_column: pm2_5_values[i],
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
