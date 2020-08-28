import argparse
import logging.config

from data_utils.settings import Settings

logger = logging.getLogger(__name__)


class Script:
    def __init__(self, args=None):
        self.parser = argparse.ArgumentParser()
        self._configure_args()
        self.args = self.parser.parse_args(args or [])
        self.settings = Settings(self.args.config) if \
            getattr(self.args, "config", None) else None

        logging.config.fileConfig(self.settings, disable_existing_loggers=False)

    def __call__(self, *args, **kwargs):
        return self.run()

    def _configure_args(self):
        self.parser.add_argument(
            "--config", "-c", help="A .ini config file.", required=True, default=None
        )
        self.add_args()

    def add_args(self):
        """Override this to add script-specific arguments."""
        pass

    def run(self):
        """Override this with the main entrypoint of the script."""
        pass
