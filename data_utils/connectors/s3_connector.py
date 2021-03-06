import logging
import boto3

logger = logging.getLogger(__name__)


class S3DownloadError(Exception):
    pass


class S3UploadError(Exception):
    pass


class S3Connector:
    def __init__(self):
        self.client = boto3.client("s3")

    def download_file(self, bucket: str, key: str, download_path: str, retry_count: int = 3) -> str:
        """Downloads existing file from S3."""
        retries = retry_count

        logger.info(f"Downloading data file: {bucket}/{key} to {download_path}.")

        while retries > 0:
            try:
                self.client.download_file(bucket, key, download_path)
                break
            except Exception as e:
                retries -= 1
                logger.exception(f"Error downloading file {key} from s3.")

                if retries == 0:
                    raise S3DownloadError(e)

        logger.info("S3 download complete.")

        return download_path

    def upload_file(self, file_name: str, bucket: str, key: str, retry_count: int = 3):
        """Helper function to upload files to S3 with basic retry logic."""
        retries = retry_count

        while retries > 0:
            try:
                self.client.upload_file(file_name, bucket, key)
                break
            except Exception as e:
                retries -= 1
                logger.exception(f"Error uploading file {file_name} to s3.")

                if retries == 0:
                    raise S3UploadError(e)
