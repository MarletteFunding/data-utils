import json
import logging
from datetime import datetime
from time import time
from typing import Dict, Any, List, Tuple

import boto3
import pymysql.cursors

from data_utils.connectors.sftp_connector import SftpConnector
from data_utils.settings import Settings


logger = logging.getLogger(__name__)


class TransferException(Exception):
    pass


class S3UploadError(Exception):
    pass


class SftpS3Interface:
    def __init__(self, settings: Settings, vendor: str = None):
        self.vendor = vendor
        self.settings = settings
        self.sftp_conn = SftpConnector(self.settings, vendor=vendor)
        self.mysql_conn = pymysql.connect(host=self.settings.get("mysql", "hostname"),
                                          user=self.settings.get("mysql", "username"),
                                          password=self.settings.get("mysql", "password"),
                                          db=self.settings.get("mysql", "database"),
                                          charset='utf8mb4',
                                          cursorclass=pymysql.cursors.DictCursor)
        self.s3_client = boto3.client("s3")

    def get_active_files(self) -> List[Dict[Any, Any]]:
        active_files = []

        self.sftp_conn.chdir(self.settings.get(f"{self.vendor}_sftp", "directory"))
        available_files = self.sftp_conn.listdir_attr()
        file_configs = self.get_file_configs()
        modified_filter = int(self.settings.get(f"{self.vendor}_sftp", "modified_buffer_minutes"))
        file_prefix = self.settings.get(f"{self.vendor}_sftp", "file_prefix")

        for file in available_files:
            for config in file_configs:
                pattern_match = f"{file_prefix}{config.get('JOB_ID').upper()}_"
                if file.filename.startswith(pattern_match) and \
                        file.st_mtime < (int(time()) - (modified_filter * 60)):
                    logger.info(f"Adding {file.filename} to process list.")
                    config["SFTP_FILENAME"] = file.filename

                    active_files.append(config)

        return active_files

    def get_file_configs(self) -> Tuple[Any]:
        with self.mysql_conn.cursor() as cursor:
            sql = f"SELECT * FROM {self.settings.get('mysql', 'table')} WHERE IS_ACTIVE = 1"
            cursor.execute(sql)
            result = cursor.fetchall()

        return result

    @staticmethod
    def convert_to_json(obj: Any) -> Any:
        """Ensure lambda return val is json serializable, best effort convert types like
        time, datetime, etc to string"""
        try:
            json_str = json.dumps(obj, default=str)
        except TypeError:
            logger.info("Return value is not json serializable.")
            return obj

        return json.loads(json_str)

    def list_active_files(self):
        active_files = self.get_active_files()
        file_names = [f.get('SFTP_FILENAME') for f in active_files]
        logger.info(f"Found the following active files in SFTP: {file_names}")
        return self.convert_to_json(active_files)

    def transfer_sftp_to_s3(self, filename: str, download_path: str, s3_bucket: str, s3_key: str) -> str:
        """Download file from SFTP server, then upload it to S3."""
        self.sftp_conn.chdir(self.settings.get(f"{self.vendor}_sftp", "directory"))

        t1 = datetime.now()
        logger.info(f"Transfer start time: {t1}")

        download_file_path = f"{download_path}{filename}"

        try:
            self.sftp_conn.get(filename, download_file_path)

            if self.settings.getboolean("file_config", "use_s3"):
                self._upload_to_s3(download_file_path, s3_bucket, s3_key)
        except Exception as e:
            logger.error(f"Error transferring file {filename}: {e}.")
            raise TransferException(e)

        t2 = datetime.now()
        logger.info(f"File transfer took {t2 - t1}")

        return download_file_path

    def _upload_to_s3(self, file_name: str, bucket: str, key: str, retry_count: int = 3):
        """Helper function to upload files to S3 with basic retry logic."""
        retries = retry_count

        while retries > 0:
            try:
                self.s3_client.upload_file(file_name, bucket, key)
                break
            except Exception as e:
                retries -= 1
                logger.exception(f"Error uploading file {file_name} to s3.")

                if retries == 0:
                    raise S3UploadError(e)
