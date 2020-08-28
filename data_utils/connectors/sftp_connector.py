import logging
from base64 import decodebytes
from io import StringIO

import pysftp
from data_utils.settings import Settings

logger = logging.getLogger(__name__)


class SftpConnector(pysftp.Connection):
    def __init__(self, settings: Settings):
        key = settings.get("sftp", "private_key")
        passphrase = settings.get("sftp", "private_key_passphrase")
        port = settings.get("sftp", "port", fallback=22)
        private_key = pysftp.RSAKey.from_private_key(StringIO(key), passphrase)
        cnopts = None

        # Add host key when not on local, where it can be stored in /.ssh/known_hosts.
        if settings.get("DEFAULT", "environment") != "local":
            fingerprint = settings.get("sftp", "host_fingerprint").encode()
            host_key = pysftp.RSAKey(data=decodebytes(fingerprint))
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys.add(settings.get("sftp", "host"), 'ssh-rsa', host_key)

        super(SftpConnector, self).__init__(host=settings.get("sftp", "host"),
                                            username=settings.get("sftp", "username"),
                                            private_key=private_key,
                                            port=int(port),
                                            cnopts=cnopts)

        logger.info("Connected to sftp.")

    def close(self):
        # Best effort
        try:
            super(SftpConnector, self).close()
        except Exception as e:
            logger.exception(e)

