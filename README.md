# dbschema

`dbschema` is a tool to run MySQL or PostgreSQL migrations automatically. Using a table, it keeps a state of previous migrations to avoid duplicates.

Features:

 - Support for MySQL and PostgreSQL
 - Optional pre and post-migration queries (for example to update privileges)
 - Multiple migrations in multiple databases can be processed as one.

## Installation

### Install `dbschema`

```bash
pip3 install dbschema
```

### Create a config file

Create the file `~/.dbschema.yml` and add your databases configuration. [See example](dbschema_sample.yml)

### Create migrations table

`dbschema` uses a table called `migrations_applied` to keep track of migrations already applied to avoid duplication.
See the schema for [MySQL](schema/mysql.sql) or [PostgreSQL](schema/postgresql.sql).

## Migrations folder structure

For each database, you need to have a migration path (setting `path` in the migration file).

Within that path you need to create one folder per migration. This folder needs to contain a file called `up.sql` with the SQL queries.

```
/path/to/migrations/db1/
|-- migration1/
|   |-- up.sql
|-- migration2/
|   |-- up.sql
|...
/path/to/migrations/db2/
|-- migration1/
|   |-- up.sql
|-- migration2/
|   |-- up.sql
|...
```

## Usage

```bash
dbschema

# or
dbschema --config /path/to/config.yml
```
