import unittest

from .. import schema_change


class Test(unittest.TestCase):

    def test_get_config(self):
        config = schema_change.get_config(
            'src/unittest/utils/config/dbschema.yml')

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


if __name__ == '__main__':
    unittest.main()
