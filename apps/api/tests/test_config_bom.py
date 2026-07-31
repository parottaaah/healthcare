import os
import tempfile
import codecs
from app.core.config import Settings

def test_settings_ignores_utf8_bom():
    # Create a temporary .env file with a UTF-8 BOM
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.env') as f:
        # Write UTF-8 BOM
        f.write(codecs.BOM_UTF8)
        # Write normal env variables
        f.write(b"DATABASE_URL=postgresql://user:pass@localhost/db\n")
        f.write(b"REDIS_URL=redis://localhost:6379/0\n")
        temp_name = f.name

    try:
        # Pass _env_file directly to the Settings constructor (Pydantic v2 compatible)
        # We also need to prevent it from reading existing environment variables
        # that might override the .env file.
        os_environ_backup = dict(os.environ)
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]
        if "REDIS_URL" in os.environ:
            del os.environ["REDIS_URL"]
            
        settings = Settings(_env_file=temp_name)
        assert settings.database_url == "postgresql://user:pass@localhost/db"
        assert settings.redis_url == "redis://localhost:6379/0"
    finally:
        os.environ.clear()
        os.environ.update(os_environ_backup)
        os.unlink(temp_name)
