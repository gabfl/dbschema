#!/usr/bin/env python3

import os
import codecs
from glob import glob

import yaml
import argparse
import pymysql.cursors
import psycopg2.extras
import psycopg2

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", type=str, help="Config file location (default: ~/.dbschema.yml)")
args = parser.parse_args()


def getConfig():
    """
        Get config file
    """

    # Set location
    configPath = '~/.dbschema.yml'
    if args.config:
        configPath = args.config

    # Check if the config file exists
    checExists(configPath)

    # Load config
    with open(configPath) as f:
        # use safe_load instead load
        config = yaml.safe_load(f)

    return config


def checExists(path, type='file'):
    """
        Check if a file or a folder exists
    """

    if type == 'file':
        if not os.path.isfile(path):
            raise RuntimeError('The file `%s` does not exist.' % path)
    else:
        if not os.path.isdir(path):
            raise RuntimeError('The folder `%s` does not exist.' % path)


def getMigrationsFiles(path):
    """
        List migrations folders
    """

    return glob(path + '*/up.sql')


def getMigrationName(file):
    """
        Returns the migration name, for example:
        `/path/to/migrations/migration1/up.sql` -> `migration1`
    """

    return os.path.basename(os.path.dirname(file))


def getMigrationSource(file):
    """
        Returns migration source code
    """

    with open(file, "r") as f:
        return f.read()


def getMysqlConnection(host, user, port, password, database):
    """
        MySQL connection
    """

    connection = pymysql.connect(host=host,
                                 user=user,
                                 port=port,
                                 password=password,
                                 db=database,
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection


def getPgConnection(host, user, port, password, database):
    """
        PostgreSQL connection
    """

    connection = psycopg2.connect(host=host,
                                  user=user,
                                  port=port,
                                  password=password,
                                  dbname=database)
    return connection


def runMigration(connection, queries):
    """
        Apply a migration to the SQL server
    """

    # Execute query
    with connection.cursor() as cursorMig:
        cursorMig.execute(queries)
        connection.commit()


def saveMigration(connection, basename):
    """
        Save a migration in `migrations_applied` table
    """

    # Prepare query
    sql = "INSERT INTO migrations_applied (name, date) VALUES (%s, NOW())"

    # Run
    with connection.cursor() as cursor:
        cursor.execute(sql, (basename,))
        connection.commit()


def isApplied(migrationsApplied, migrationName):
    """
        Check if a migration we want to run is already in the list of applied migrations
    """

    return [True for migrationApplied in migrationsApplied if migrationApplied['name'] == migrationName]


def getMigrationsApplied(engine, connection):
    """
        Get list of migrations already applied
    """

    try:
        # Get cursor based on engine
        if engine == 'postgresql':
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cursor = connection.cursor()

        sql = "SELECT id, name, date FROM migrations_applied"
        cursor.execute(sql)
        rows = cursor.fetchall()
        # print (rows);
        return rows
    except psycopg2.ProgrammingError:
        raise RuntimeError('The table `migrations_applied` is missing. Please refer to the project documentation at https://github.com/gabfl/dbschema.')
    except pymysql.err.ProgrammingError:
        raise RuntimeError('The table `migrations_applied` is missing. Please refer to the project documentation at https://github.com/gabfl/dbschema.')


def loopThruMigrations(engine, path, connection):
    """
        Get the list of migrations already applied
        then loop thru migrations found in `path` and apply them
    """

    # Get migrations applied
    migrationsApplied = getMigrationsApplied(engine, connection)
    # print(migrationsApplied)

    # Get migrations folder
    for file in getMigrationsFiles(path):
        # Set vars
        basename = os.path.basename(os.path.dirname(file))

        # Skip migrations if they are already applied
        if isApplied(migrationsApplied, basename):
            continue

        # Get migration source
        source = getMigrationSource(file)
        # print (source);

        # Run migration
        runMigration(connection, source)

        # Save migration
        saveMigration(connection, basename)

        # Log
        print('   -> Migration ' + basename + ' applied')


def applyMigrations(engine, host, user, port, password, db, path, preMigration, postMigration):
    """
        Connect to the database and apply all migrations in a chronological order
    """

    if engine == 'mysql':
        # Connection
        connection = getMysqlConnection(host, user, port, password, db)
    elif engine == 'postgresql':
        # Connection
        connection = getPgConnection(host, user, port, password, db)
    else:
        raise RuntimeError('`%s` is not a valid engine.' % engine)

    # Run pre migration queries
    if preMigration:
        runMigration(connection, preMigration)

    # Find an apply migrations recursively
    loopThruMigrations(engine, path, connection)

    # Run post migration queries
    if postMigration:
        runMigration(connection, postMigration)

    # Log
    print(' * Migrations applied')


def main():
    # Load config
    config = getConfig()
    databases = config['databases']

    for database in databases:
        # Set vars
        engine = databases[database].get('engine', 'mysql')
        host = databases[database].get('127.0.0.1', 'localhost')
        port = databases[database].get('port', 3306)
        user = databases[database].get('user')
        password = databases[database].get('password')
        db = databases[database].get('db')
        path = databases[database].get('path')
        preMigration = databases[database].get('pre_migration')
        postMigration = databases[database].get('post_migration')

        # Check if the migration path exists
        checExists(path, 'dir')

        print(' * Applying migrations for ' + engine + ' -> ' + db)

        applyMigrations(engine, host, user, port, password, db, path, preMigration, postMigration)


if __name__ == "__main__":
    main()
