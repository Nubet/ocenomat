from alembic import context
from app.core.config import Settings
from app.core.database import Base, create_database_engine
from app.modules.assessments import models as assessments_models  # noqa: F401
from app.modules.catalog import models as catalog_models  # noqa: F401
from app.modules.employees import models as employees_models  # noqa: F401
from app.modules.users import models as users_models  # noqa: F401

settings = Settings()
target_metadata = Base.metadata

if context.is_offline_mode():
    if settings.database_url is None:
        raise ValueError("KOMPAS_DATABASE_URL is required")
    context.configure(
        url=settings.database_url.get_secret_value(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_database_engine(settings)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()
