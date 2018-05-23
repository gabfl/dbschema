# dbschema

[![Build Status](https://travis-ci.org/gabfl/dbschema.svg?branch=master)](https://travis-ci.org/gabfl/dbschema)

`dbschema` is a tool to run MySQL or PostgreSQL migrations automatically. Using a table, it keeps a state of previous migrations to avoid duplicates.

Features:

 - Support for MySQL and PostgreSQL
 - Optional pre and post-migration queries (for example to update privileges)
 - Multiple migrations in multiple databases can be processed as one.

## Installation

### Install `dbschema`

```bash
# Install required packages
apt-get update
apt-get install --yes libpq-dev gcc python3-dev

pip3 install dbschema
```

### Create a config file

Create the file `~/.dbschema.yml` and add your databases configuration. [See example](dbschema_sample.yml)

### Create migrations table

`dbschema` uses a table called `migrations_applied` to keep track of migrations already applied to avoid duplication.
See the schema for [MySQL](schema/mysql.sql) or [PostgreSQL](schema/postgresql.sql).

## Migrations folder structure

For each database, you need to have a migration path (setting `path` in the migration file).

Within that path you need to create one folder per migration. This folder must contain a file called `up.sql` with the SQL queries and optionally a file called `down.sql` for rollbacks.

```
/path/to/migrations/db1/
|-- migration1/
|   |-- up.sql
|   |-- down.sql
|-- migration2/
|   |-- up.sql
|...
/path/to/migrations/db2/
|-- migration1/
|   |-- up.sql
|-- migration2/
|   |-- up.sql
|   |-- down.sql
|...
```

## Usage

### Apply pending migrations

```bash
dbschema

# or to specify a config file path
dbschema --config /path/to/config.yml

# or to migrate only a specific database
dbschema --tag db1
```

### Rollback

```bash
dbschema --tag db1 --rollback migration1
```

## Example

```bash
$ dbschema
  * Applying migrations for db1 (`test` on postgresql)
    -> Migration `migration1` applied
    -> Migration `migration2` applied
    -> Migration `migration3` applied
  * Migrations applied
  * Applying migrations for db2 (`test` on mysql)
    -> Migration `migration1` applied
    -> Migration `migration2` applied
    -> Migration `migration3` applied
  * Migrations applied
$
$ dbschema --tag db2 --rollback migration1
  * Rolling back mysql -> `migration1`
    -> Migration `migration1` has been rolled back
$
```
