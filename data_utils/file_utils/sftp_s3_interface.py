import logging
from datetime import datetime

from data_utils.connectors.s3_connector import S3Connector
from data_utils.connectors.sftp_connector import SftpConnector
from data_utils.settings import Settings

logger = logging.getLogger(__name__)


class TransferException(Exception):
    pass


class SftpS3Interface:
    def __init__(self, settings: Settings, vendor: str = None):
        self.section = f"{vendor}_sftp" if vendor else "sftp"
        self.settings = settings
        logger.info("Connecting to SFTP...")
        self.sftp_conn = SftpConnector(self.settings, vendor=vendor)
        logger.info("Connected to sftp successfully")
        self.s3_client = S3Connector()

    def transfer_sftp_to_s3(self, filename: str, download_path: str, s3_bucket: str, s3_key: str,
                            sftp_directory: str) -> str:
        """Download file from SFTP server, then upload it to S3."""
        self.sftp_conn.chdir(sftp_directory)

        t1 = datetime.now()
        logger.info(f"Transfer start time: {t1}")

        download_file_path = f"{download_path}{filename}"

        try:
            self.sftp_conn.get(filename, download_file_path)

            if self.settings.getboolean("file_config", "use_s3"):
                self.s3_client.upload_file(download_file_path, s3_bucket, s3_key)
        except Exception as e:
            logger.error(f"Error transferring file {filename}: {e}.")
            raise TransferException(e)

        t2 = datetime.now()
        logger.info(f"File transfer took {t2 - t1}")

        return download_file_path

    def transfer_s3_to_sftp(self, s3_bucket: str, s3_key: str, file_name: str, sftp_directory: str) -> str:
        """Download file from S3, then put it on SFTP server"""
        self.sftp_conn.chdir(sftp_directory)

        t1 = datetime.now()
        logger.info(f"Transfer start time: {t1}")

        file_path = f"/tmp/{file_name}"

        self.s3_client.download_file(s3_bucket, s3_key, file_path)

        try:
            self.sftp_conn.put(file_path)
        except Exception as e:
            logger.error(f"Error transferring file {file_name}: {e}.")
            raise TransferException(e)

        t2 = datetime.now()
        logger.info(f"File transfer took {t2 - t1}")

        return file_name
