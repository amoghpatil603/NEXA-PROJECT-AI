import sys

content = open("backend/database/pg_database.py").read()
content = content.replace(
"""    except Exception as e:
        logger.warning(f"PostgreSQL connection to {DB_HOST}:{DB_PORT} failed, using Mock DB connection: {e}")
        return MockPgConnection()""",
"""    except Exception as e:
        logger.error(f"PostgreSQL connection to {DB_HOST}:{DB_PORT} failed: {e}")
        raise e"""
)
open("backend/database/pg_database.py", "w").write(content)
