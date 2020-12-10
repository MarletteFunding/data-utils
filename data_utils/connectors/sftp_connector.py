import logging
from base64 import decodebytes
from io import StringIO

import pysftp
from data_utils.settings import Settings

logger = logging.getLogger(__name__)


class SftpConnector(pysftp.Connection):
    def __init__(self, settings: Settings, *, vendor: str = None):
        section = f"{self.vendor}_sftp" if vendor else "sftp"
        key = settings.get(section, "private_key")
        passphrase = settings.get(section, "private_key_passphrase")
        port = settings.get(section, "port", fallback=22)
        private_key = pysftp.RSAKey.from_private_key(StringIO(key), passphrase)
        cnopts = None

        # Add host key when not on local, where it can be stored in /.ssh/known_hosts.
        if settings.get("DEFAULT", "environment") != "local":
            fingerprint = settings.get(section, "host_fingerprint").encode()
            host_key = pysftp.RSAKey(data=decodebytes(fingerprint))
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys.add(settings.get(section, "host"), 'ssh-rsa', host_key)

        super(SftpConnector, self).__init__(host=settings.get(section, "host"),
                                            username=settings.get(section, "username"),
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

