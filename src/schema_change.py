#!/usr/bin/env python3

import os
import codecs
from glob import glob

import yaml
import argparse
import pymysql.cursors
import pymysql.constants.CLIENT
import psycopg2.extras
import psycopg2


def get_config(override):
    """
        Get config file
    """

    # Set location
    config_path = os.path.expanduser('~') + '/.dbschema.yml'
    if override:
        config_path = override

    # Check if the config file exists
    check_exists(config_path)

    # Load config
    with open(config_path) as f:
        # use safe_load instead load
        config = yaml.safe_load(f)

    return config


def check_exists(path, type='file'):
    """
        Check if a file or a folder exists
    """

    if type == 'file':
        if not os.path.isfile(path):
            raise RuntimeError('The file `%s` does not exist.' % path)
    else:
        if not os.path.isdir(path):
            raise RuntimeError('The folder `%s` does not exist.' % path)

    return True


def get_migrations_files(path):
    """
        List migrations folders
    """

    migrations = glob(path + '*/up.sql')
    migrations.sort()

    return migrations


def add_slash(path):
    """
        Ensure that the path ends with a slash
    """

    if not path.endswith('/'):
        return path + '/'

    return path


def get_migration_name(file):
    """
        Returns the migration name, for example:
        `/path/to/migrations/migration1/up.sql` -> `migration1`
    """

    return os.path.basename(os.path.dirname(file))


def get_migration_source(file):
    """
        Returns migration source code
    """

    with open(file, "r") as f:
        return f.read()


def get_connection(engine, host, user, port, password, database, ssl={}):
    """
        Returns a PostgreSQL or MySQL connection
    """

    if engine == 'mysql':
        # Connection
        return get_mysql_connection(host, user, port, password, database, ssl)
    elif engine == 'postgresql':
        # Connection
        return get_pg_connection(host, user, port, password, database, ssl)
    else:
        raise RuntimeError('`%s` is not a valid engine.' % engine)


def get_mysql_connection(host, user, port, password, database, ssl={}):
    """
        MySQL connection
    """

    return pymysql.connect(host=host,
                           user=user,
                           port=port,
                           password=password,
                           db=database,
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor,
                           client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS,
                           ssl=ssl
                           )


def get_pg_connection(host, user, port, password, database, ssl={}):
    """
        PostgreSQL connection
    """

    return psycopg2.connect(host=host,
                            user=user,
                            port=port,
                            password=password,
                            dbname=database,
                            sslmode=ssl.get('sslmode', None),
                            sslcert=ssl.get('sslcert', None),
                            sslkey=ssl.get('sslkey', None),
                            sslrootcert=ssl.get('sslrootcert', None),
                            )


def run_migration(connection, queries):
    """
        Apply a migration to the SQL server
    """

    # Execute query
    with connection.cursor() as cursorMig:
        cursorMig.execute(queries)
        connection.commit()

    return True


def save_migration(connection, basename):
    """
        Save a migration in `migrations_applied` table
    """

    # Prepare query
    sql = "INSERT INTO migrations_applied (name, date) VALUES (%s, NOW())"

    # Run
    with connection.cursor() as cursor:
        cursor.execute(sql, (basename,))
        connection.commit()

    return True


def delete_migration(connection, basename):
    """
        Delete a migration in `migrations_applied` table
    """

    # Prepare query
    sql = "DELETE FROM migrations_applied WHERE name = %s"

    # Run
    with connection.cursor() as cursor:
        cursor.execute(sql, (basename,))
        connection.commit()

    return True


def is_applied(migrations_applied, migration_name):
    """
        Check if a migration we want to run is already in the list of applied migrations
    """

    return [True for migration in migrations_applied if migration['name'] == migration_name]


def get_migrations_applied(engine, connection):
    """
        Get list of migrations already applied
    """

    try:
        # Get cursor based on engine
        if engine == 'postgresql':
            cursor = connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cursor = connection.cursor()

        sql = "SELECT id, name, date FROM migrations_applied"
        cursor.execute(sql)
        rows = cursor.fetchall()
        # print (rows);
        return rows
    except psycopg2.ProgrammingError:
        raise RuntimeError(
            'The table `migrations_applied` is missing. Please refer to the project documentation at https://github.com/gabfl/dbschema.')
    except pymysql.err.ProgrammingError:
        raise RuntimeError(
            'The table `migrations_applied` is missing. Please refer to the project documentation at https://github.com/gabfl/dbschema.')


def apply_migrations(engine, connection, path):
    """
        Apply all migrations in a chronological order
    """

    # Get migrations applied
    migrations_applied = get_migrations_applied(engine, connection)
    # print(migrationsApplied)

    # Get migrations folder
    for file in get_migrations_files(path):
        # Set vars
        basename = os.path.basename(os.path.dirname(file))

        # Skip migrations if they are already applied
        if is_applied(migrations_applied, basename):
            continue

        # Get migration source
        source = get_migration_source(file)
        # print (source);

        # Run migration
        run_migration(connection, source)

        # Save migration
        save_migration(connection, basename)

        # Log
        print('   -> Migration `%s` applied' % (basename))

    # Log
    print(' * Migrations applied')

    return True


def rollback_migration(engine, connection, path, migration_to_rollback):
    """
        Rollback a migration
    """

    # Get migrations applied
    migrations_applied = get_migrations_applied(engine, connection)

    # Ensure that the migration was previously applied
    if not is_applied(migrations_applied, migration_to_rollback):
        raise RuntimeError(
            '`%s` is not in the list of previously applied migrations.' % (migration_to_rollback))

    # Rollback file
    file = path + migration_to_rollback + '/down.sql'

    # Ensure that the file exists
    check_exists(file)

    # Set vars
    basename = os.path.basename(os.path.dirname(file))

    # Get migration source
    source = get_migration_source(file)
    # print (source);

    # Run migration rollback
    run_migration(connection, source)

    # Delete migration
    delete_migration(connection, basename)

    # Log
    print('   -> Migration `%s` has been rolled back' % (basename))

    return True


def get_ssl(database):
    """
        Returns SSL options for the selected engine
    """

    # Set available keys per engine
    if database['engine'] == 'postgresql':
        keys = ['sslmode', 'sslcert', 'sslkey',
                'sslrootcert', 'sslcrl', 'sslcompression']
    else:
        keys = ['ssl_ca', 'ssl_capath', 'ssl_cert', 'ssl_key',
                'ssl_cipher', 'ssl_check_hostname']

    # Loop thru keys
    ssl = {}
    for key in keys:
        value = database.get(key, None)
        if value is not None:
            ssl[key] = value

    return ssl


def apply(config_override=None, tag_override=None, rollback=None, skip_missing=None):
    """
        Look thru migrations and apply them
    """

    # Load config
    config = get_config(config_override)
    databases = config['databases']

    # If we are rolling back, ensure that we have a database tag
    if rollback and not tag_override:
        raise RuntimeError(
            'To rollback a migration you need to specify the database tag with `--tag`')

    for tag in databases:
        # If a tag is specified, skip other tags
        if tag_override and tag_override != tag:
            continue

        # Set vars
        engine = databases[tag].get('engine', 'mysql')
        host = databases[tag].get('host', 'localhost')
        port = databases[tag].get('port', 3306)
        user = databases[tag].get('user')
        password = databases[tag].get('password')
        db = databases[tag].get('db')
        path = add_slash(databases[tag].get('path'))
        pre_migration = databases[tag].get('pre_migration')
        post_migration = databases[tag].get('post_migration')

        # Check if the migration path exists
        if skip_missing:
            try:
                check_exists(path, 'dir')
            except RuntimeError:
                continue
        else:
            check_exists(path, 'dir')

        # Get database connection
        connection = get_connection(
            engine, host, user, port, password, db, get_ssl(databases[tag]))

        # Run pre migration queries
        if pre_migration:
            run_migration(connection, pre_migration)

        if rollback:
            print(' * Rolling back %s (`%s` on %s)' % (tag, db, engine))

            rollback_migration(engine, connection, path, rollback)
        else:
            print(' * Applying migrations for %s (`%s` on %s)' %
                  (tag, db, engine))

            apply_migrations(engine, connection, path)

        # Run post migration queries
        if post_migration:
            run_migration(connection, post_migration)

    return True


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str,
                        help="Config file location (default: ~/.dbschema.yml)")
    parser.add_argument("-t", "--tag", type=str, help="Database tag")
    parser.add_argument("-r", "--rollback", type=str,
                        help="Rollback a migration")
    parser.add_argument("-s", "--skip_missing", action='store_true',
                        help="Skip missing migration folders")
    args = parser.parse_args()

    apply(args.config, args.tag, args.rollback, args.skip_missing)


if __name__ == "__main__":
    main()
