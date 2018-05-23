import unittest
import psycopg2
import pymysql

from .. import schema_change


class Test(unittest.TestCase):

    config_path = 'src/unittest/utils/config/dbschema.yml'

    def test_get_config(self):
        config = schema_change.get_config(self.config_path)

        self.assertIsInstance(config, dict)

    def test_check_exists(self):
        self.assertTrue(schema_change.check_exists(
            'src/unittest/utils/migrations/mysql/one/up.sql'))
        self.assertTrue(schema_change.check_exists(
            'src/unittest/utils/migrations/mysql/one/', 'dir'))

    def test_get_migrations_files(self):
        migration_files = schema_change.get_migrations_files(
            'src/unittest/utils/migrations/mysql/')

        self.assertTrue(
            'src/unittest/utils/migrations/mysql/one/up.sql' in migration_files)
        self.assertTrue(
            'src/unittest/utils/migrations/mysql/two/up.sql' in migration_files)
        self.assertTrue(
            'src/unittest/utils/migrations/mysql/three/up.sql' in migration_files)

    def test_get_migration_name(self):
        self.assertEqual(schema_change.get_migration_name(
            'src/unittest/utils/migrations/mysql/one/up.sql'), 'one')

    def test_get_migration_source(self):
        self.assertEqual(schema_change.get_migration_source(
            'src/unittest/utils/migrations/mysql/one/down.sql').strip(), 'DROP TABLE one;')

    def test_get_connection(self):
        config = schema_change.get_config(self.config_path)
        databases = config['databases']

        for tag in databases:
            # Set vars
            engine = databases[tag].get('engine', 'mysql')
            host = databases[tag].get('host', 'localhost')
            port = databases[tag].get('port', 3306)
            user = databases[tag].get('user')
            password = databases[tag].get('password')
            db = databases[tag].get('db')

            # Get database connection
            connection = schema_change.get_connection(
                engine, host, user, port, password, db, schema_change.get_ssl(databases[tag]))

            if engine == 'postgresql':
                self.assertIsInstance(
                    connection, psycopg2.extensions.connection)
            else:
                self.assertIsInstance(
                    connection, pymysql.connections.Connection)

    def test_get_mysql_connection(self):
        config = schema_change.get_config(self.config_path)
        database = config['databases']['tag_mysql']

        # Get database connection
        connection = schema_change.get_mysql_connection(
            database['host'], database['user'], database['port'], database['password'], database['db'], schema_change.get_ssl(database))

        self.assertIsInstance(
            connection, pymysql.connections.Connection)

    def test_get_pg_connection(self):
        config = schema_change.get_config(self.config_path)
        database = config['databases']['tag_postgresql']

        # Get database connection
        connection = schema_change.get_pg_connection(
            database['host'], database['user'], database['port'], database['password'], database['db'], schema_change.get_ssl(database))

        self.assertIsInstance(
            connection, psycopg2.extensions.connection)

    def test_run_migration(self):
        config = schema_change.get_config(self.config_path)
        database = config['databases']['tag_postgresql']

        # Get database connection
        connection = schema_change.get_pg_connection(
            database['host'], database['user'], database['port'], database['password'], database['db'], schema_change.get_ssl(database))

        self.assertTrue(schema_change.run_migration(connection, 'SELECT 1'))

    def test_save_migration(self):
        config = schema_change.get_config(self.config_path)
        database = config['databases']['tag_postgresql']

        # Get database connection
        connection = schema_change.get_pg_connection(
            database['host'], database['user'], database['port'], database['password'], database['db'], schema_change.get_ssl(database))

        self.assertTrue(schema_change.save_migration(
            connection, 'some_migration'))

    def test_delete_migration(self):
        config = schema_change.get_config(self.config_path)
        database = config['databases']['tag_postgresql']

        # Get database connection
        connection = schema_change.get_pg_connection(
            database['host'], database['user'], database['port'], database['password'], database['db'], schema_change.get_ssl(database))

        self.assertTrue(schema_change.delete_migration(
            connection, 'some_migration'))

    def test_is_applied(self):
        migrations_applied = [
            {
                'name': 'one'
            },
            {
                'name': 'two'
            },
            {
                'name': 'three'
            },
        ]

        self.assertTrue(schema_change.is_applied(migrations_applied, 'three'))
        self.assertFalse(schema_change.is_applied(migrations_applied, 'four'))


if __name__ == '__main__':
    unittest.main()
