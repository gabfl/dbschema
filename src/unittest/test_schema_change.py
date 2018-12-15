import unittest
import psycopg2
import pymysql
import datetime

from .. import schema_change


class Test(unittest.TestCase):

    config_path = 'src/unittest/utils/config/dbschema.yml'
    config_path_empty_db = 'src/unittest/utils/config/dbschema_empty_db.yml'

    def test_get_config(self):
        config = schema_change.get_config(self.config_path)

        self.assertIsInstance(config, dict)

    def test_get_config_2(self):
        # Test loading from home directory
        config = schema_change.get_config()

        self.assertIsInstance(config, dict)

    def test_check_exists(self):
        self.assertTrue(schema_change.check_exists(
            'src/unittest/utils/migrations/mysql/one/up.sql'))
        self.assertTrue(schema_change.check_exists(
            'src/unittest/utils/migrations/mysql/one/', 'dir'))

        # Check exceptions for non existent
        self.assertRaises(RuntimeError, schema_change.check_exists,
                          'src/unittest/utils/non_existent')
        self.assertRaises(RuntimeError, schema_change.check_exists,
                          'src/unittest/utils/non_existent', 'dir')

    def test_get_migrations_files(self):
        migration_files = schema_change.get_migrations_files(
            'src/unittest/utils/migrations/mysql/')

        self.assertTrue(
            'src/unittest/utils/migrations/mysql/one/up.sql' in migration_files)
        self.assertTrue(
            'src/unittest/utils/migrations/mysql/two/up.sql' in migration_files)
        self.assertTrue(
            'src/unittest/utils/migrations/mysql/three/up.sql' in migration_files)

    def test_add_slash(self):
        self.assertEqual(schema_change.add_slash('some/path')[-1], '/')
        self.assertEqual(schema_change.add_slash('some/path/')[-1], '/')

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

        # Test exception for non existing engine
        self.assertRaises(RuntimeError, schema_change.get_connection,
                          'unknown_engine', None, None, None, None, None)

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

    def test_parse_statements(self):
        """ Test single query """

        queries = """SELECT 1;"""
        parsed = schema_change.parse_statements(queries, engine='mysql')

        assert len(parsed) == 1
        assert parsed[0] == 'SELECT 1;'

    def test_parse_statements_2(self):
        """ Test single query without delimiter """

        queries = """SELECT 1"""
        parsed = schema_change.parse_statements(queries, engine='mysql')

        assert len(parsed) == 1
        assert parsed[0] == 'SELECT 1'

    def test_parse_statements_3(self):
        """ Test multiple queries and comment removal """

        queries = """
        SELECT 1;
        -- Some comment
        SELECT 2;
        """
        parsed = schema_change.parse_statements(queries, engine='mysql')

        assert len(parsed) == 2
        assert parsed[0] == 'SELECT 1;'
        assert parsed[1] == 'SELECT 2;'

    def test_parse_statements_4(self):
        """ Test delimiter change  """

        queries = """
        SELECT 1;
        -- Some comment
        DELIMITER $$
        SELECT 2$$
        DELIMITER ;
        SELECT 3;
        """
        parsed = schema_change.parse_statements(queries, engine='mysql')

        assert len(parsed) == 3
        assert parsed[0] == 'SELECT 1;'
        assert parsed[1] == 'SELECT 2;'
        assert parsed[2] == 'SELECT 3;'

    def test_parse_statements_5(self):
        """ Test for MySQL stored function """

        queries = """
        SELECT 1;

        DELIMITER $$

        CREATE FUNCTION CustomerLevel(p_creditLimit double) RETURNS VARCHAR(10)
        BEGIN
            RETURN 1;
        END$$

        DELIMITER ;

        SELECT 2;
        """
        parsed = schema_change.parse_statements(queries, engine='mysql')

        assert len(parsed) == 3
        assert parsed[0] == 'SELECT 1;'
        assert parsed[1] == """CREATE FUNCTION CustomerLevel(p_creditLimit double) RETURNS VARCHAR(10)
BEGIN
RETURN 1;
END;"""
        assert parsed[2] == 'SELECT 2;'

    def test_parse_statements_6(self):
        """ Test for PostgreSQL stored function """

        queries = """
        SELECT 1;

        CREATE OR REPLACE FUNCTION some function(a int, b bigint)
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        BEGIN
            UPDATE table
            SET something = b
            WHERE id = a;
            RETURN FOUND;
        END;
        $$;

        SELECT 2;
        """
        parsed = schema_change.parse_statements(
            queries, engine='postgresql')

        assert len(parsed) == 3
        assert parsed[0] == 'SELECT 1;'
        assert parsed[1] == """CREATE OR REPLACE FUNCTION some function(a int, b bigint)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
UPDATE table
SET something = b
WHERE id = a;
RETURN FOUND;
END;
$$;"""
        assert parsed[2] == 'SELECT 2;'

    def test_run_migration(self):
        config = schema_change.get_config(self.config_path)
        database = config['databases']['tag_postgresql']

        # Get database connection
        connection = schema_change.get_pg_connection(
            database['host'], database['user'], database['port'], database['password'], database['db'], schema_change.get_ssl(database))

        self.assertTrue(schema_change.run_migration(
            connection, 'SELECT 1', engine='postgresql'))

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

    def test_get_migrations_applied(self):
        config = schema_change.get_config(self.config_path)
        database = config['databases']['tag_postgresql']

        # Get database connection
        connection = schema_change.get_pg_connection(
            database['host'], database['user'], database['port'], database['password'], database['db'], schema_change.get_ssl(database))

        # Add fake migrations
        schema_change.save_migration(connection, 'some_migration')
        schema_change.save_migration(connection, 'some_migration_2')

        migrations_applied = schema_change.get_migrations_applied(
            database['engine'], connection)

        for migration in migrations_applied:
            self.assertIsInstance(migration['id'], int)
            self.assertIsInstance(migration['name'], str)
            self.assertIsInstance(migration['date'], datetime.datetime)

        # Delete fake migrations
        schema_change.delete_migration(connection, 'some_migration')
        schema_change.delete_migration(connection, 'some_migration_2')

    def test_get_migrations_applied_2(self):
        # Only loading empty databases to trigger an exception
        config = schema_change.get_config(self.config_path_empty_db)

        for tag in config['databases']:
            database = config['databases'][tag]

            # Get database connection
            connection = schema_change.get_connection(
                database['engine'], database['host'], database['user'], database['port'], database['password'], database['db'], schema_change.get_ssl(database))

            # Test exception for non existing engine
            self.assertRaises(RuntimeError, schema_change.get_migrations_applied,
                              database['engine'], connection)

    def test_apply_migrations(self):
        config = schema_change.get_config(self.config_path)
        database = config['databases']['tag_postgresql']

        # Get database connection
        connection = schema_change.get_pg_connection(
            database['host'], database['user'], database['port'], database['password'], database['db'], schema_change.get_ssl(database))

        self.assertTrue(schema_change.apply_migrations(
            database['engine'], connection, database['path']))

    def test_rollback_migration(self):
        config = schema_change.get_config(self.config_path)
        database = config['databases']['tag_postgresql']

        # Get database connection
        connection = schema_change.get_pg_connection(
            database['host'], database['user'], database['port'], database['password'], database['db'], schema_change.get_ssl(database))

        self.assertTrue(schema_change.rollback_migration(
            database['engine'], connection, database['path'], 'one'))

        # Test exception for non existing engine
        self.assertRaises(RuntimeError, schema_change.rollback_migration,
                          database['engine'], connection, database['path'], 'non_existent')

    def test_get_ssl(self):
        config = schema_change.get_config(self.config_path)

        for tag in config['databases']:
            database = config['databases'][tag]

            self.assertIsInstance(schema_change.get_ssl(database), dict)

    def test_apply(self):
        self.assertTrue(schema_change.apply(config_override=self.config_path,
                                            skip_missing=True))
        self.assertTrue(schema_change.apply(config_override=self.config_path,
                                            tag_override='tag_mysql'))
        self.assertTrue(schema_change.apply(config_override=self.config_path,
                                            tag_override='tag_mysql',
                                            rollback='one'))
        self.assertTrue(schema_change.apply(config_override=self.config_path,
                                            skip_missing=True))

        # Test exception for rollback without a tag
        self.assertRaises(RuntimeError, schema_change.apply,
                          self.config_path, None, 'one')


if __name__ == '__main__':
    unittest.main()
