from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy import create_engine

from alembic import context

import os
from dotenv import load_dotenv
from data.models import Base


load_dotenv()

host = os.getenv("FULLTEXT_HOST", None)
port = os.getenv("FULLTEXT_PORT", None)
db = os.getenv("FULLTEXT_DB", None)
user = os.getenv("FULLTEXT_USER", None)
password = os.getenv("FULLTEXT_PASSWORD", None)

missing = []
if not host:
    missing.append("FULLTEXT_HOST")
if not port:
    missing.append("FULLTEXT_PORT")
if not db:
    missing.append("FULLTEXT_DB")
if not user:
    missing.append("FULLTEXT_USER")
if not password:
    missing.append("FULLTEXT_PASSWORD")
if missing:
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
url = f"postgresql://{user}:{password}@{host}:{port}/{db}"

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the configs file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the configs, defined by the needs of env.py,
# can be acquired:
# my_important_option = configs.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
