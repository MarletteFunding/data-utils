import logging
import os

import snowflake.connector
from data_utils.settings import Settings
from snowflake.connector.cursor import SnowflakeCursor, DictCursor

logger = logging.getLogger(__name__)


class SnowflakeConnector:
    def __init__(self, settings: Settings):
        self.conn = snowflake.connector.connect(
            user=settings.get("snowflake", "username"),
            password=settings.get("snowflake", "password"),
            account=settings.get("snowflake", "account"),
            region=settings.get("snowflake", "region"),
            warehouse=settings.get("snowflake", "warehouse"),
            database=settings.get("snowflake", "database"),
            role=settings.get("snowflake", "role"),
            schema=settings.get("snowflake", "schema"),
            client_session_keep_alive=settings.getboolean("snowflake", "keep_alive", fallback=False)
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def query(self, querystring: str):
        logger.info(f"Executing query: {querystring}")
        return self.conn.cursor().execute(querystring)

    def query_dict(self, querystring: str):
        logger.info(f"Executing query: {querystring}")
        return self.conn.cursor(DictCursor).execute(querystring)

    def stage_file(self, file_path: str, stage_name: str, table_name: str = None,
                   file_format: str = None, copy: bool = False) -> None:
        logger.info(f"Staging file {file_path} to stage {stage_name}")

        try:
            self.conn.cursor().execute(f"PUT file:///{file_path} @{stage_name}")
        except Exception as e:
            logger.error(f"Error staging file: {e}.")
            raise e

        if copy and table_name:
            try:
                self.conn.cursor().execute(f"COPY INTO {table_name} FROM @{stage_name} "
                                           f"FILES = ('{file_path}') FILE_FORMAT = {file_format}")
            except Exception as e:
                logger.error(f"Error copying file: {e}.")
                raise e

    def copy_staged_file(self, stage_name: str, table_name: str) -> None:
        pass

