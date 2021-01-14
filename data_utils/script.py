import argparse
import logging.config

from data_utils.settings import Settings
from data_utils.connectors.slack_connector import SlackConnector

logger = logging.getLogger(__name__)


class Script:
    def __init__(self, args=None):
        self.parser = argparse.ArgumentParser()
        self._configure_args()
        self.args = self.parser.parse_args(args or [])
        self.settings = Settings(self.args.config) if getattr(self.args, "config", None) else None
        self.slack_connector = SlackConnector(self.settings)

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
        self.extract()
        self.transform()
        self.load()

    def extract(self):
        """Override with your code"""
        pass

    def transform(self):
        """Override with your code"""
        pass

    def load(self):
        """Override with your code"""
        pass
