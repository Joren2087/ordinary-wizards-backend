# Database Migrations

Database schema migrations are handled by flask-migrate which uses [Alembic](https://alembic.sqlalchemy.org/en/latest/) as its backend. Alembic is a lightweight database migration tool for SQLAlchemy.

All migrations (up & downgrade) are found in the `/migrations/versions` directory. Each migration file is named with a timestamp and a description of the migration.

You can create one yourself by modifying the SQLAlchemy model structure (thus editing the source code) and running the following command with `APP_AUTOMIGRATE=false` and `APP_DISABLE_SCHEMA_VALIDATION=true`:

```bash
flask db migrate -m "migration description"
```

This will create a new migration file in the `/migrations/versions` directory. You can then apply this migration to the database by running:

```bash
flask db upgrade [revision_id]
```

You can check the wether the current database is up-to-date with the source code by running:

```bash
flask db check
```

You can see the current migration history by running:

```bash
flask db history
```

If you want to downgrade a migration, you can run:

```bash
flask db downgrade [revision_id]
```

For a full list of commands, see the [Flask-Migrate documentation](https://flask-migrate.readthedocs.io/en/latest/).

## Setting up a new database
Follow the steps in the [README.md](/README.md) to setup a new database. After the database is created and SQLAlchemy is able to properly connect, you can run the following command to create the final database schema iteravely:

```bash
flask db upgrade
```